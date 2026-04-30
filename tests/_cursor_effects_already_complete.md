# Cursor Click Effects — Already Complete

All cursor click effects from the "Add Cursor Effects" tutorial were already
implemented by a previous track. 37 cursor/click effects are registered in
`src/camtasia/effects/cursor.py`:

- 15 `@register_effect` decorated classes (CursorMotionBlur, CursorShadow,
  CursorPhysics, LeftClickScaling, CursorColor, CursorGlow, CursorHighlight,
  CursorIsolation, CursorMagnify, CursorSpotlight, CursorGradient, CursorLens,
  CursorNegative, CursorSmoothing, RightClickScaling)
- 22 factory-generated click effects (LeftClickBurst1-4, RightClickBurst1-4,
  LeftClickZoom, RightClickZoom, LeftClickRings, RightClickRings,
  LeftClickRipple, RightClickRipple, LeftClickScope, RightClickScope,
  LeftClickTarget, RightClickTarget, LeftClickWarp, RightClickWarp,
  LeftClickSound, RightClickSound)

Only `CursorPathCreator` remains unimplemented (separate roadmap item under
"Customize the Cursor Path").
