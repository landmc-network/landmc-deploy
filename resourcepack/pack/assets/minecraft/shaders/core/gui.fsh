#version 330

// The client's own gui.fsh, plus one discard: the box it fills behind the sidebar.
//
// That box is not a texture, so no image in a pack replaces it - but every flat coloured quad
// in the interface is drawn by this shader, and this one can be told apart from the others by
// four things at once:
//
//   * the layer it is on. Measured, not guessed: this client draws it at zero or below.
//   * the half of the screen it is on. The scoreboard is against the right edge; the chat
//     background is the same colour on the same layer, and is on the left.
//   * its colour, which is pure black.
//   * its opacity, which is the quarter or so the "background opacity" option gives it. The
//     sheet drawn behind an open inventory is also black on this layer and reaches both halves
//     of the screen, but it is far more opaque than this - which is what keeps that screen
//     from losing its right half.
//
// Four coincidences rather than one, and still a heuristic: a shader is not told what it is
// drawing. Deleting this file and gui.vsh puts the client's own behaviour back, and the panel
// in landmc:ui is opaque enough to cover the box on its own if it ever comes to that.

// Can't moj_import in things used during startup, when resource packs don't exist.
// This is a copy of dynamicimports.glsl
layout(std140) uniform DynamicTransforms {
    mat4 ModelViewMat;
    vec4 ColorModulator;
    vec3 ModelOffset;
    mat4 TextureMat;
};

in vec4 vertexColor;
in vec2 screenPosition;
flat in float layer;

out vec4 fragColor;

/** Above this the quad is a sheet over a whole screen, not a background behind a few lines. */
const float MAXIMUM_OPACITY = 0.6;

void main() {
    vec4 color = vertexColor;
    if (color.a == 0.0) {
        discard;
    }

    bool onBoardLayer = layer <= 0.0;
    bool rightHalf = screenPosition.x > 0.0;
    bool black = color.r + color.g + color.b < 0.05;
    bool faint = color.a < MAXIMUM_OPACITY;

    if (onBoardLayer && rightHalf && black && faint) {
        discard;
    }

    fragColor = color * ColorModulator;
}
