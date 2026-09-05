#version 150

// Vanilla's GUI vertex shader, with one addition: the box the client fills behind the sidebar
// is made fully transparent.
//
// That box is not a texture, so there is nothing in a pack to replace with a blank image - but
// a pack may replace a core shader, and every flat coloured quad in the interface goes through
// this one. The sidebar's box can be picked out of them by where it is drawn and how deep:
// hard against the right edge of the screen, in the vertical band the board occupies, at the
// depth the client reserves for that layer. Setting its alpha to zero removes it while leaving
// the rest of the interface alone.
//
// This is a heuristic and worth knowing as one. It identifies the sidebar by position rather
// than by name, because a shader is not told what it is drawing; another flat quad in the same
// place at the same depth would go with it. Nothing in the vanilla interface is, which is why
// it is safe in practice rather than in principle.
//
// It is also tied to the shape of this file in the client that reads it. A version whose own
// gui.vsh differs will not compile this one - if the interface misbehaves, delete this file,
// rebuild the pack, and everything returns to how it was.

in vec3 Position;
in vec4 Color;

uniform mat4 ModelViewMat;
uniform mat4 ProjMat;

out vec4 vertexColor;

// The depth range the client draws the sidebar's background at.
const float SIDEBAR_NEAR = 1000.0;
const float SIDEBAR_FAR = 2750.0;

void main() {
    gl_Position = ProjMat * ModelViewMat * vec4(Position, 1.0);
    vertexColor = Color;

    bool rightHalf = gl_Position.x > 0.0 && gl_Position.x <= 1.0;
    bool boardBand = gl_Position.y > -0.5 && gl_Position.y < 0.85;
    bool boardDepth = Position.z > SIDEBAR_NEAR && Position.z < SIDEBAR_FAR;

    if (rightHalf && boardBand && boardDepth) {
        vertexColor.a = 0.0;
    }
}
