"""Product-page interactions needed to add one eBay item to the cart."""

import random
from dataclasses import dataclass

from playwright.sync_api import Locator, TimeoutError

from pages.base_page import BasePage


class CartAdditionError(RuntimeError):
    """Raised when the page does not confirm that an item reached the cart."""


class ProductUnavailableError(CartAdditionError):
    """Raised when eBay identifies the current listing as ended or unavailable."""


@dataclass(frozen=True)
class VariantSelection:
    """One reproducible product-variant choice."""

    name: str
    value: str


class ProductPage(BasePage):
    """Select available product variants and add one item to the cart."""

    _VARIANT_SELECTS = "select:is(.x-msku__select-box, [aria-required='true'], [required])"
    _VARIANT_LISTBOX_BUTTONS = "button[aria-haspopup='listbox']"
    _CART_COUNT = "#gh-cart-n"
    _ADD_TO_CART_NAME = "Add to cart"
    _UNAVAILABLE_TEXTS = (
        "This listing was ended by the seller",
        "This item is no longer available",
    )

    @property
    def variant_selects(self) -> Locator:
        """Return visible native variant controls from the current product layout."""
        return self.page.locator(self._VARIANT_SELECTS)

    @property
    def add_to_cart_control(self) -> Locator:
        """Return the visible Add to cart button or link."""
        button = self.page.get_by_role(
            "button",
            name=self._ADD_TO_CART_NAME,
            exact=True,
        )
        link = self.page.get_by_role(
            "link",
            name=self._ADD_TO_CART_NAME,
            exact=True,
        )
        return button.or_(link).first

    def select_available_variants(self, rng: random.Random) -> tuple[VariantSelection, ...]:
        """Choose one enabled value from every visible required variant control."""
        selections: list[VariantSelection] = []

        for index in range(self.variant_selects.count()):
            select = self.variant_selects.nth(index)
            if not select.is_visible() or not select.is_enabled():
                continue

            available_options = self._available_options(select)
            if not available_options:
                name = self._variant_name(select, index)
                raise CartAdditionError(f"No available values for required variant {name!r}")

            chosen_value, chosen_label = rng.choice(available_options)
            select.select_option(value=chosen_value)
            selections.append(
                VariantSelection(
                    name=self._variant_name(select, index),
                    value=chosen_label,
                )
            )

        selections.extend(self._select_custom_listbox_variants(rng))
        return tuple(selections)

    def _select_custom_listbox_variants(
        self,
        rng: random.Random,
    ) -> list[VariantSelection]:
        """Choose values from eBay's button-based Size/Width listboxes."""
        selections: list[VariantSelection] = []
        controls = self.page.locator(self._VARIANT_LISTBOX_BUTTONS)

        for index in range(controls.count()):
            control = controls.nth(index)
            if not control.is_visible() or not control.is_enabled():
                continue

            variant_name, separator, current_value = control.inner_text().partition(":")
            if not separator or current_value.strip().casefold() not in {"select", "choose"}:
                continue

            variant_name = variant_name.strip()
            control.click()
            try:
                self.page.locator("[role='option']:visible").first.wait_for(
                    state="visible",
                    timeout=5_000,
                )
            except TimeoutError as exc:
                raise CartAdditionError(
                    f"No available values for required variant {variant_name!r}"
                ) from exc
            available_options = self._available_listbox_options()
            if not available_options:
                raise CartAdditionError(
                    f"No available values for required variant {variant_name!r}"
                )

            chosen_option, chosen_label = rng.choice(available_options)
            chosen_option.click()
            selections.append(VariantSelection(name=variant_name, value=chosen_label))

        return selections

    def require_available_listing(self) -> None:
        """Stop early when eBay explicitly marks the listing unavailable."""
        for unavailable_text in self._UNAVAILABLE_TEXTS:
            if self.page.get_by_text(unavailable_text, exact=False).first.is_visible():
                raise ProductUnavailableError(
                    f"The listing at {self.page.url!r} is no longer available"
                )

    def add_to_cart(self) -> None:
        """Click Add to cart and require visible evidence of a successful addition."""
        self.require_available_listing()
        control = self.add_to_cart_control
        if not control.is_visible() or not control.is_enabled():
            raise CartAdditionError("Add to cart control is not available")

        previous_url = self.page.url
        previous_count = self._read_cart_count()
        control.click()

        try:
            outcome = self.page.wait_for_function(
                """
                ({ previousUrl, previousCount, countSelector, errorText }) => {
                    const bodyText = document.body?.innerText || '';
                    const normalizedBodyText = bodyText.toLowerCase();
                    if (normalizedBodyText.includes('added to cart')
                        || normalizedBodyText.includes('added to your cart')) {
                        return 'confirmed';
                    }
                    if (bodyText.includes(errorText)) {
                        return 'error';
                    }

                    const countNode = document.querySelector(countSelector);
                    const countText = countNode?.textContent || '';
                    const digits = [...countText]
                        .filter(character => character >= '0' && character <= '9')
                        .join('');
                    const currentCount = digits ? Number(digits) : null;
                    if (previousCount !== null) {
                        return currentCount !== null && currentCount > previousCount
                            ? 'confirmed'
                            : false;
                    }

                    const reachedCart = location.href !== previousUrl
                        && location.href.toLowerCase().includes('cart');
                    return reachedCart && currentCount !== null && currentCount > 0
                        ? 'confirmed'
                        : false;
                }
                """,
                arg={
                    "previousUrl": previous_url,
                    "previousCount": previous_count,
                    "countSelector": self._CART_COUNT,
                    "errorText": self.error_page.MESSAGE,
                },
                timeout=5_000,
            )
        except TimeoutError as exc:
            raise CartAdditionError(
                f"The item at {previous_url!r} was not confirmed in the cart"
            ) from exc

        if outcome.json_value() == "error":
            self.error_page.go_to_home_if_displayed()
            raise CartAdditionError(
                f"eBay returned its error page before confirming the item at {previous_url!r}"
            )

    def _available_options(self, select: Locator) -> list[tuple[str, str]]:
        available: list[tuple[str, str]] = []
        options = select.locator("option")

        for option_index in range(options.count()):
            option = options.nth(option_index)
            value = option.get_attribute("value")
            label = option.inner_text().strip()
            if option.is_disabled() or not value or value == "-1":
                continue
            if self._is_placeholder(label):
                continue
            available.append((value, label))

        return available

    def _available_listbox_options(self) -> list[tuple[Locator, str]]:
        available: list[tuple[Locator, str]] = []
        options = self.page.get_by_role("option")

        for option_index in range(options.count()):
            option = options.nth(option_index)
            if not option.is_visible() or not option.is_enabled():
                continue
            if option.get_attribute("aria-disabled") == "true":
                continue
            if "disabled" in (option.get_attribute("class") or "").lower():
                continue

            label = self._without_selected_suffix(option.inner_text().strip())
            if not label or self._is_placeholder(label):
                continue
            available.append((option, label))

        return available

    @staticmethod
    def _variant_name(select: Locator, index: int) -> str:
        return (
            select.get_attribute("aria-label")
            or select.get_attribute("name")
            or f"variant-{index + 1}"
        )

    def _read_cart_count(self) -> int | None:
        count = self.page.locator(self._CART_COUNT).first
        if not count.count() or not count.is_visible():
            return None

        digits = "".join(character for character in count.inner_text() if character.isdigit())
        return int(digits) if digits else None

    @staticmethod
    def _is_placeholder(label: str) -> bool:
        first_word = label.casefold().split(maxsplit=1)[0] if label else ""
        return first_word in {"select", "choose"}

    @staticmethod
    def _without_selected_suffix(label: str) -> str:
        suffix = " selected"
        if label.casefold().endswith(suffix):
            return label[: -len(suffix)].rstrip()
        return label
