#version 330

// The client's own gui.vsh, with one addition: the box it fills behind the sidebar is given an
// alpha of zero, and gui.fsh discards anything with an alpha of zero.
//
// That box is not a texture, so no image in a pack replaces it. A pack may replace a core
// shader, though, and every flat coloured quad in the interface is drawn by this one - so the
// sidebar's box can be picked out of them and dropped.
//
// Everything above main() is copied from the client verbatim and must stay that way. The
// uniforms are a block layout, not loose values, and a shader that declares them differently
// does not link: that is exactly how the first attempt at this failed, by carrying a version
// 150 file with plain `uniform mat4` into a client that wants version 330 and a UBO.
//
// The test is on the layer alone, and deliberately not on where the quad is on screen. Alpha
// is a vertex attribute: the fragments between two vertices get the average of them, so a
// screen-position test on a box that reaches past the edge of the tested band clears the
// vertices inside it, keeps the ones outside, and leaves a fade across the difference. That is
// what a leftover strip of the old background is. The layer is the same number at all four
// corners, so the box either goes entirely or stays entirely.
//
// It remains a heuristic: a shader is not told what it is drawing, and anything else on this
// layer would go with it.

// Can't moj_import in things used during startup, when resource packs don't exist.
// This is a copy of dynamicimports.glsl and projection.glsl
layout(std140) uniform DynamicTransforms {
    mat4 ModelViewMat;
    vec4 ColorModulator;
    vec3 ModelOffset;
    mat4 TextureMat;
};
layout(std140) uniform Projection {
    mat4 ProjMat;
};

in vec3 Position;
in vec4 Color;

out vec4 vertexColor;

// The layers the interface reserves for the scoreboard. Below this is the world and the hud
// drawn over it; above it are tooltips and open screens, which have to keep their backgrounds.
const float SIDEBAR_NEAR = 1000.0;
const float SIDEBAR_FAR = 2750.0;

void main() {
    gl_Position = ProjMat * ModelViewMat * vec4(Position, 1.0);

    vertexColor = Color;

    if (Position.z > SIDEBAR_NEAR && Position.z < SIDEBAR_FAR) {
        vertexColor.a = 0.0;
    }
}
