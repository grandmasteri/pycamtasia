from __future__ import annotations

from numbers import Real

from marshmallow import Schema, fields, post_load
from marshmallow_oneofschema import OneOfSchema

from camtasia.color import RGBA, hex_rgb

COLOR_KEY = "color"

COMPENSATION_KEY = "clrCompensation"
COLOR_ALPHA_KEY = "color-alpha"
COLOR_RED_KEY = "color-red"
COLOR_GREEN_KEY = "color-green"
COLOR_BLUE_KEY = "color-blue"
DEFRINGE_KEY = "defringe"
TOLERANCE_KEY = "tolerance"
SOFTNESS_KEY = "softness"
INVERT_EFFECT_KEY = "invertEffect"
CHROMA_KEY_NAME = "ChromaKey"
VISUAL_EFFECTS_CATEGORY = "categoryVisualEffects"





def rgba(argument: str) -> tuple[int, int, int, int]:
    """Parse a hex color string into an RGBA tuple, defaulting alpha to 255."""
    channels = hex_rgb(argument)
    if len(channels) == 3:
        return (*channels, 255)
    return channels


def rgb(argument: str) -> tuple[int, int, int]:
    """Parse a hex color string into an RGB tuple, raising if alpha is not 0xFF."""
    channels = hex_rgb(argument)
    if len(channels) == 4 and channels[3] != 255:
        raise ValueError("Alpha argument not 0xFF for RGB color")
    return channels[:3]


class Effect:
    """Base class for Camtasia effects."""

    def __init__(self, *, name: str, category: str) -> None:
        """Initialize an effect with a name and category."""
        self._name = name
        self._category = category

    @property
    def name(self) -> str:
        """Return the effect name."""
        return self._name

    @property
    def category(self) -> str:
        """Return the effect category."""
        return self._category

    def __repr__(self) -> str:
        """Return a string representation of the effect."""
        return f"{type(self).__name__}(name={self.name!r}, category={self.category!r})"

    def __eq__(self, other: object) -> bool:
        """Check equality based on the effect's key."""
        if not isinstance(other, type(self)):
            return NotImplemented
        return self._key() == other._key()

    def __hash__(self) -> int:
        """Return a hash based on the effect's key."""
        return hash(self._key())

    def _key(self) -> tuple[str, str]:
        return (self.name, self.category)


class VisualEffect(Effect):
    """An effect in the visual effects category."""

    def __init__(self, *, name: str) -> None:
        """Initialize a visual effect with the given name."""
        super().__init__(name=name, category=VISUAL_EFFECTS_CATEGORY)


class ChromaKeyEffect(VisualEffect):
    """A chroma key (green screen) visual effect with configurable color and thresholds."""

    DEFAULT_TOLERANCE = 0.1
    MINIMUM_TOLERANCE = 0.0
    MAXIMUM_TOLERANCE = 1.0

    DEFAULT_SOFTNESS = 0.1
    MINIMUM_SOFTNESS = 0.0
    MAXIMUM_SOFTNESS = 1.0

    DEFAULT_DEFRINGE = 0.0
    MINIMUM_DEFRINGE = -1.0
    MAXIMUM_DEFRINGE = 1.0

    DEFAULT_INVERTED = False

    DEFAULT_COLOR = RGBA(0, 255, 0, 255)

    DEFAULT_COMPENSATION = 0.0  # Confusingly, this is called "hue" in the Camtasia GUI.
    MINIMUM_COMPENSATION = 0.0
    MAXIMUM_COMPENSATION = 1.0

    def __init__(
        self,
        tolerance: float | None = None,
        softness: float | None = None,
        hue: RGBA | str | None = None,
        defringe: float | None = None,
        inverted: bool | None = None,
        compensation: float | None = None,
    ) -> None:
        """Initialize a chroma key effect with optional color and threshold parameters."""
        super().__init__(name=CHROMA_KEY_NAME)

        if tolerance is None:
            tolerance = self.DEFAULT_TOLERANCE

        if not (self.MINIMUM_TOLERANCE <= tolerance <= self.MAXIMUM_TOLERANCE):
            raise ValueError(
                f"{self.name} tolerance out of range {self.MINIMUM_TOLERANCE} "
                f"to {self.MAXIMUM_TOLERANCE}"
            )

        if softness is None:
            softness = self.DEFAULT_SOFTNESS

        if not (self.MINIMUM_SOFTNESS <= softness <= self.MAXIMUM_SOFTNESS):
            raise ValueError(
                f"{self.name} softness out of range {self.MINIMUM_SOFTNESS} "
                f"to {self.MAXIMUM_SOFTNESS}"
            )

        if defringe is None:
            defringe = self.DEFAULT_DEFRINGE

        if not (self.MINIMUM_DEFRINGE <= defringe <= self.MAXIMUM_DEFRINGE):
            raise ValueError(
                f"{self.name} defringe out of range {self.MINIMUM_DEFRINGE} "
                f"to {self.MAXIMUM_DEFRINGE}"
            )

        if compensation is None:
            compensation = self.DEFAULT_COMPENSATION

        if not (self.MINIMUM_COMPENSATION <= compensation <= self.MAXIMUM_COMPENSATION):
            raise ValueError(
                f"{self.name} compensation out of range {self.MINIMUM_COMPENSATION} "
                f"to {self.MAXIMUM_COMPENSATION}"
            )

        if inverted is None:
            inverted = self.DEFAULT_INVERTED

        if hue is None:
            hue = self.DEFAULT_COLOR
        elif isinstance(hue, str):
            hue = RGBA.from_hex(hue)

        self._tolerance = tolerance
        self._softness = softness
        self._defringe = defringe
        self._inverted = inverted
        self._hue = hue
        self._compensation = compensation

    @property
    def tolerance(self) -> float:
        """Return the color tolerance threshold."""
        return self._tolerance

    @property
    def softness(self) -> float:
        """Return the edge softness value."""
        return self._softness

    @property
    def defringe(self) -> float:
        """Return the defringe adjustment value."""
        return self._defringe

    @property
    def inverted(self) -> bool:
        """Return whether the effect is inverted."""
        return self._inverted

    @property
    def compensation(self) -> float:
        """Return the hue compensation value."""
        return self._compensation

    @property
    def hue(self) -> RGBA:
        """Return the key color as an RGBA value."""
        return self._hue

    @property
    def alpha(self) -> float:
        """Return the key color alpha channel as a normalized float."""
        return self._hue.alpha / RGBA.MAXIMUM_CHANNEL

    @property
    def red(self) -> float:
        """Return the key color red channel as a normalized float."""
        return self._hue.red / RGBA.MAXIMUM_CHANNEL

    @property
    def green(self) -> float:
        """Return the key color green channel as a normalized float."""
        return self._hue.green / RGBA.MAXIMUM_CHANNEL

    @property
    def blue(self) -> float:
        """Return the key color blue channel as a normalized float."""
        return self._hue.blue / RGBA.MAXIMUM_CHANNEL

    @property
    def parameters(self) -> Parameters:
        """Return a Parameters proxy for this effect."""
        return Parameters(self)

    @property
    def metadata(self) -> dict[str, str]:
        """Return the default metadata dictionary for serialization."""
        return {
            f"default-{self.name}-{key}": self._metadata_value(value) for key, value in self._metadata().items()
        }

    @staticmethod
    def _metadata_value(value: object) -> str:
        """Render a metadata value in the way Camtasia expects
        """
        if isinstance(value, Real):
            if value == 0:
                value = 0
        return str(value).replace(" ", "")


    def _metadata(self) -> dict[str, object]:
        return {
            COLOR_KEY: self._hue.as_tuple(),
            DEFRINGE_KEY: self._defringe,
            INVERT_EFFECT_KEY: int(self._inverted),
            SOFTNESS_KEY: self._softness,
            TOLERANCE_KEY: self._tolerance,
            COMPENSATION_KEY: self._compensation,
        }

    def _key(self) -> tuple:
        return super()._key() + (
            self.tolerance,
            self.softness,
            self.defringe,
            self.inverted,
            self.compensation,
            self.red,
            self.green,
            self.blue,
            self.alpha,
        )

    def __repr__(self) -> str:
        """Return a detailed string representation of the chroma key effect."""
        return (
            f"{type(self).__name__}(tolerance={self.tolerance}, softness={self.softness}, "
            f"hue={self.hue}, defringe={self.defringe}, inverted={self.inverted}, "
            f"compensation={self.compensation})"
        )


class Parameters:
    """Proxy that delegates attribute access to a ChromaKeyEffect."""

    def __init__(self, effect: ChromaKeyEffect) -> None:
        """Initialize with the backing ChromaKeyEffect instance."""
        self._effect = effect

    def __getattr__(self, name: str) -> object:
        """Delegate attribute lookup to the wrapped effect."""
        return getattr(self._effect, name)


class ChromaKeyEffectParametersSchema(Schema):
    """Marshmallow schema for serializing ChromaKeyEffect parameters."""
    compensation = fields.Float(data_key=COMPENSATION_KEY)
    alpha = fields.Float(data_key=COLOR_ALPHA_KEY)
    red = fields.Float(data_key=COLOR_RED_KEY)
    green = fields.Float(data_key=COLOR_GREEN_KEY)
    blue = fields.Float(data_key=COLOR_BLUE_KEY)
    defringe = fields.Float(data_key=DEFRINGE_KEY)
    enabled = fields.Constant(1)
    inverted = fields.Function(
        data_key=INVERT_EFFECT_KEY,
        serialize=lambda obj: float(obj.inverted),
        deserialize=lambda b: bool(b)
    )
    softness = fields.Float(data_key=SOFTNESS_KEY)
    tolerance = fields.Float(data_key=TOLERANCE_KEY)


class ChromaKeyEffectSchema(Schema):
    """Marshmallow schema for serializing and deserializing a ChromaKeyEffect."""

    category = fields.Str(data_key="category")
    bypassed = fields.Boolean(dump_default=False)
    parameters = fields.Nested(ChromaKeyEffectParametersSchema)

    @post_load
    def make_chroma_key_effect(self, data: dict, **kwargs: object) -> ChromaKeyEffect:
        """Construct a ChromaKeyEffect from deserialized data."""
        parameters = data["parameters"]
        return ChromaKeyEffect(
            tolerance=parameters["tolerance"],
            softness=parameters["softness"],
            hue=RGBA.from_floats(
                red=parameters["red"],
                green=parameters["green"],
                blue=parameters["blue"],
                alpha=parameters["alpha"],
            ),
            defringe=parameters["defringe"],
            inverted=parameters["inverted"],
            compensation=parameters["compensation"]
        )


class EffectSchema(OneOfSchema):
    """Polymorphic schema that dispatches to the correct effect schema by name."""
    type_schemas = {
        CHROMA_KEY_NAME: ChromaKeyEffectSchema,
    }

    type_field = "effectName"

    def get_obj_type(self, obj: Effect) -> str:
        """Return the effect name used to select the schema type."""
        return obj.name

