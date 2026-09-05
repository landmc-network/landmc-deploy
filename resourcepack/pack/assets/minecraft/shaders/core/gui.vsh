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
// The test itself is a heuristic and worth knowing as one. A shader is not told what it is
// drawing, so the sidebar is identified by where it is on the screen and how deep it is in the
// interface's own stack of layers. Nothing else in the vanilla interface sits there, which
// makes it safe in practice rather than in principle.

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

    // Right half of the screen, in the band the board occupies, on the scoreboard's layer.
    bool rightHalf = gl_Position.x > 0.0 && gl_Position.x <= 1.0;
    bool boardBand = gl_Position.y > -0.5 && gl_Position.y < 0.85;
    bool boardLayer = Position.z > SIDEBAR_NEAR && Position.z < SIDEBAR_FAR;

    if (rightHalf && boardBand && boardLayer) {
        vertexColor.a = 0.0;
    }
}
