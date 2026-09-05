#version 330

// The client's own gui.vsh, plus the two values gui.fsh needs to recognise the box behind the
// sidebar and throw it away.
//
// Everything above main() is copied from the client verbatim and must stay that way: the
// uniforms are a block layout, not loose values, and a shader that restates them differently
// does not link.
//
// The test itself is in the fragment shader rather than here, and that is not a detail. Alpha
// set on a vertex is averaged across the quad, so a test that some corners pass and others fail
// leaves a fade instead of a clean removal - the leftover strip of old background that this
// went through twice. A fragment either is inside the region or is not.

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

/** Where this fragment is on the screen. The interface is drawn flat, so w is 1 and this is
    already normalised: -1 at the left edge, 1 at the right. */
out vec2 screenPosition;

/** The layer the quad is drawn on. Flat, because it is a property of the quad, not of a point
    inside it - the client puts the scoreboard's background at zero or below. */
flat out float layer;

void main() {
    gl_Position = ProjMat * ModelViewMat * vec4(Position, 1.0);

    vertexColor = Color;
    screenPosition = gl_Position.xy;
    layer = Position.z;
}
