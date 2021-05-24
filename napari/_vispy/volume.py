from vispy.color import get_colormap
from vispy.scene.visuals import create_visual_node
from vispy.visuals.shaders import Function

from .vendored import VolumeVisual as BaseVolumeVisual
from .vendored.volume import ADDITIVE_SNIPPETS
from .vendored.volume import FRAG_SHADER as FRAG_SHADER_VOLUME
from .vendored.volume import ISO_SNIPPETS, MIP_SNIPPETS, TRANSLUCENT_SNIPPETS
from .vendored.volume import frag_dict as frag_dict_volume

# Fragment shader for rendering arbitrary planes through volumes.
# A ray is cast perpendicular to plane and computation is performed
# this fragment shader is designed to be compatible with the snippets used in
# volumetric rendering from vispy/napari
FRAG_SHADER_PLANE = """
// uniforms
uniform $sampler_type u_volumetex;
uniform vec3 u_shape;
uniform vec2 clim;
uniform float gamma;
uniform float u_threshold;
uniform float u_attenuation; // todo add to vispy from napari
uniform float u_relative_step_size;

//varyings
// varying vec3 v_texcoord;
varying vec3 v_position;
varying vec4 v_nearpos;
varying vec4 v_farpos;

// uniforms for lighting. Hard coded until we figure out how to do lights
const vec4 u_ambient = vec4(0.2, 0.2, 0.2, 1.0);
const vec4 u_diffuse = vec4(0.8, 0.2, 0.2, 1.0);
const vec4 u_specular = vec4(1.0, 1.0, 1.0, 1.0);
const float u_shininess = 40.0;

// uniforms for plane definition. 
// Hard coded until we figure out the plane shader.
// defined in data coordinates.
const vec3 u_plane_normal = vec3(1.0, 1.0, 1.0);
const vec3 u_plane_position = vec3(64.0, 64.0, 64.0);
const float u_plane_thickness = 10.0;

//varying vec3 lightDirs[1];

// global holding view direction in local coordinates
vec3 view_ray;

float rand(vec2 co)
{{
    // Create a pseudo-random number between 0 and 1.
    // http://stackoverflow.com/questions/4200224
    return fract(sin(dot(co.xy ,vec2(12.9898, 78.233))) * 43758.5453);
}}

float colorToVal(vec4 color1)
{{
    return color1.g; // todo: why did I have this abstraction in visvis?
}}

vec4 applyColormap(float data) {{
    if (clim.x < clim.y) {{
        data = clamp(data, clim.x, clim.y);
    }} else {{
        data = clamp(data, clim.y, clim.x);
    }}

    data = (data - clim.x) / (clim.y - clim.x);
    return $cmap(pow(data, gamma));
}}


vec4 calculateColor(vec4 betterColor, vec3 loc, vec3 step)
{{   
    // Calculate color by incorporating lighting
    vec4 color1;
    vec4 color2;

    // View direction
    vec3 V = normalize(view_ray);

    // calculate normal vector from gradient
    vec3 N; // normal
    color1 = $sample( u_volumetex, loc+vec3(-step[0],0.0,0.0) );
    color2 = $sample( u_volumetex, loc+vec3(step[0],0.0,0.0) );
    N[0] = colorToVal(color1) - colorToVal(color2);
    betterColor = max(max(color1, color2),betterColor);
    color1 = $sample( u_volumetex, loc+vec3(0.0,-step[1],0.0) );
    color2 = $sample( u_volumetex, loc+vec3(0.0,step[1],0.0) );
    N[1] = colorToVal(color1) - colorToVal(color2);
    betterColor = max(max(color1, color2),betterColor);
    color1 = $sample( u_volumetex, loc+vec3(0.0,0.0,-step[2]) );
    color2 = $sample( u_volumetex, loc+vec3(0.0,0.0,step[2]) );
    N[2] = colorToVal(color1) - colorToVal(color2);
    betterColor = max(max(color1, color2),betterColor);
    float gm = length(N); // gradient magnitude
    N = normalize(N);

    // Flip normal so it points towards viewer
    float Nselect = float(dot(N,V) > 0.0);
    N = (2.0*Nselect - 1.0) * N;  // ==  Nselect * N - (1.0-Nselect)*N;

    // Get color of the texture (albeido)
    color1 = betterColor;
    color2 = color1;
    // todo: parametrise color1_to_color2

    // Init colors
    vec4 ambient_color = vec4(0.0, 0.0, 0.0, 0.0);
    vec4 diffuse_color = vec4(0.0, 0.0, 0.0, 0.0);
    vec4 specular_color = vec4(0.0, 0.0, 0.0, 0.0);
    vec4 final_color;

    // todo: allow multiple light, define lights on viewvox or subscene
    int nlights = 1; 
    for (int i=0; i<nlights; i++)
    {{ 
        // Get light direction (make sure to prevent zero devision)
        vec3 L = normalize(view_ray);  //lightDirs[i]; 
        float lightEnabled = float( length(L) > 0.0 );
        L = normalize(L+(1.0-lightEnabled));

        // Calculate lighting properties
        float lambertTerm = clamp( dot(N,L), 0.0, 1.0 );
        vec3 H = normalize(L+V); // Halfway vector
        float specularTerm = pow( max(dot(H,N),0.0), u_shininess);

        // Calculate mask
        float mask1 = lightEnabled;

        // Calculate colors
        ambient_color +=  mask1 * u_ambient;  // * gl_LightSource[i].ambient;
        diffuse_color +=  mask1 * lambertTerm;
        specular_color += mask1 * specularTerm * u_specular;
    }}

    // Calculate final color by componing different components
    final_color = color2 * ( ambient_color + diffuse_color) + specular_color;
    final_color.a = color2.a;

    // Done
    return final_color;
}}

vec3 intersectLinePlane(vec3 lineStart, 
                        vec3 lineVector, 
                        vec3 planePosition, 
                        vec3 planeNormal) {{
    // function to find the intersection between a line and a plane
    // line is defined by position and vector
    // plane is defined by position and normal vector
    // https://en.wikipedia.org/wiki/Line%E2%80%93plane_intersection

    // find scale factor for line vector
    float scaleFactor = dot(planePosition - lineStart, planeNormal) / 
                        dot(lineVector, planeNormal);

    // calculate intersection
    return lineStart + ( scaleFactor * lineVector );
}}


// for some reason, this has to be the last function in order for the
// filters to be inserted in the correct place...

void main() {{
    vec3 farpos = v_farpos.xyz / v_farpos.w;
    vec3 nearpos = v_nearpos.xyz / v_nearpos.w;

    // Calculate unit vector pointing in the view direction through this
    // fragment.
    view_ray = normalize(farpos.xyz - nearpos.xyz);

    // find intersection of view ray with plane in data coordinates
    vec3 intersection = intersectLinePlane(v_position.xyz, view_ray, 
                                           u_plane_position, u_plane_normal);
    // and texture coordinates
    vec3 intersection_tex = intersection / u_shape;
    
    // discard if not in volume
    if (intersection_tex.x > 1.0 )
        discard;
    if (intersection_tex.y > 1.0 )
        discard;
    if (intersection_tex.z > 1.0 )
        discard;
    if (intersection_tex.x < 0.0 )
        discard;
    if (intersection_tex.y < 0.0 )
        discard;
    if (intersection_tex.z < 0.0 )
        discard;

    // Decide how many steps to take
    int nsteps = int(u_plane_thickness / u_relative_step_size + 0.5);
    float f_nsteps = float(nsteps);
    if( nsteps < 1 )
        discard;

    // Get step vector and starting location in texture coordinates
    // step vector is along plane normal
    vec3 N = normalize(u_plane_normal);
    vec3 step = N / u_shape;
    vec3 start_loc = intersection_tex - ((step * f_nsteps) / 2);

    {before_loop}

    // This outer loop seems necessary on some systems for large
    // datasets. Ugly, but it works ...
    vec3 loc = start_loc;
    int iter = 0;
    while (iter < nsteps) {{
        for (iter=iter; iter<nsteps; iter++)
        {{
            // Get sample color
            vec4 color = $sample(u_volumetex, loc);
            float val = color.g;

            {in_loop}

            // Advance location deeper into the volume
            loc += step;
        }}
    }}

    {after_loop}

    /* Set depth value - from visvis TODO
    int iter_depth = int(maxi);
    // Calculate end position in world coordinates
    vec4 position2 = vertexPosition;
    position2.xyz += ray*shape*float(iter_depth);
    // Project to device coordinates and set fragment depth
    vec4 iproj = gl_ModelViewProjectionMatrix * position2;
    iproj.z /= iproj.w;
    gl_FragDepth = (iproj.z+1.0)/2.0;
    */
}}


"""  # noqa

BaseVolume = create_visual_node(BaseVolumeVisual)

MIP_FRAG_SHADER_PLANE = FRAG_SHADER_PLANE.format(**MIP_SNIPPETS)
TRANSLUCENT_FRAG_SHADER_PLANE = FRAG_SHADER_PLANE.format(
    **TRANSLUCENT_SNIPPETS
)
ADDITIVE_FRAG_SHADER_PLANE = FRAG_SHADER_PLANE.format(**ADDITIVE_SNIPPETS)
ISO_FRAG_SHADER_PLANE = FRAG_SHADER_PLANE.format(**ISO_SNIPPETS)

frag_dict_plane = {
    'mip': MIP_FRAG_SHADER_PLANE,
    'iso': ISO_FRAG_SHADER_PLANE,
    'translucent': TRANSLUCENT_FRAG_SHADER_PLANE,
    'additive': ADDITIVE_FRAG_SHADER_PLANE,
}

ATTENUATED_MIP_SNIPPETS = dict(
    before_loop="""
        float maxval = -99999.0; // The maximum encountered value
        float sumval = 0.0; // The sum of the encountered values
        float scaled = 0.0; // The scaled value
        int maxi = 0;  // Where the maximum value was encountered
        vec3 maxloc = vec3(0.0);  // Location where the maximum value was encountered
        """,
    in_loop="""
        sumval = sumval + val;
        scaled = val * exp(-u_attenuation * (sumval - 1) / u_relative_step_size);
        if( scaled > maxval ) {
            maxval = scaled;
            maxi = iter;
            maxloc = loc;
        }
        """,
    after_loop="""
        gl_FragColor = applyColormap(maxval);
        """,
)
ATTENUATED_MIP_FRAG_SHADER_VOLUME = FRAG_SHADER_VOLUME.format(
    **ATTENUATED_MIP_SNIPPETS
)
ATTENUATED_MIP_FRAG_SHADER_PLANE = FRAG_SHADER_PLANE.format(
    **ATTENUATED_MIP_SNIPPETS
)

frag_dict_volume['attenuated_mip'] = ATTENUATED_MIP_FRAG_SHADER_VOLUME
frag_dict_plane['attenuated_mip'] = ATTENUATED_MIP_FRAG_SHADER_PLANE

MINIP_SNIPPETS = dict(
    before_loop="""
        float minval = 99999.0; // The minimum encountered value
        int mini = 0;  // Where the minimum value was encountered
        """,
    in_loop="""
        if( val < minval ) {
            minval = val;
            mini = iter;
        }
        """,
    after_loop="""
        // Refine search for min value
        loc = start_loc + step * (float(mini) - 0.5);
        for (int i=0; i<10; i++) {
            minval = min(minval, $sample(u_volumetex, loc).g);
            loc += step * 0.1;
        }
        gl_FragColor = applyColormap(minval);
        """,
)

MINIP_FRAG_SHADER_VOLUME = FRAG_SHADER_VOLUME.format(**MINIP_SNIPPETS)
MINIP_FRAG_SHADER_PLANE = FRAG_SHADER_PLANE.format(**MINIP_SNIPPETS)

frag_dict_volume['minip'] = MINIP_FRAG_SHADER_VOLUME
frag_dict_plane['minip'] = MINIP_FRAG_SHADER_PLANE

AVG_SNIPPETS = dict(
    before_loop="""
        float n = 0; // Counter for encountered values
        float meanval = 0.0; // The mean of encountered values
        float prev_mean = 0.0; // Variable to store the previous incremental mean
        """,
    in_loop="""
        // Incremental mean value used for numerical stability
        n += 1; // Increment the counter
        prev_mean = meanval; // Update the mean for previous iteration
        meanval = prev_mean + (val - prev_mean) / n; // Calculate the mean
        """,
    after_loop="""
        // Apply colormap on mean value
        gl_FragColor = applyColormap(meanval);
        """,
)
AVG_FRAG_SHADER_VOLUME = FRAG_SHADER_VOLUME.format(**AVG_SNIPPETS)
AVG_FRAG_SHADER_PLANE = FRAG_SHADER_PLANE.format(**AVG_SNIPPETS)

frag_dict_volume['average'] = AVG_FRAG_SHADER_VOLUME
frag_dict_plane['average'] = AVG_FRAG_SHADER_PLANE


# Custom volume class is needed for better 3D rendering
class Volume(BaseVolume):
    def __init__(self, *args, **kwargs):
        self._attenuation = 1.0
        self._shader = 'plane'
        super().__init__(*args, **kwargs)

    @property
    def cmap(self):
        return self._cmap

    @cmap.setter
    def cmap(self, cmap):
        self._cmap = get_colormap(cmap)
        self.shared_program.frag['cmap'] = Function(self._cmap.glsl_map)
        # Colormap change fix
        self.shared_program['texture2D_LUT'] = (
            self.cmap.texture_lut()
            if (hasattr(self.cmap, 'texture_lut'))
            else None
        )
        self.update()

    @property
    def threshold(self):
        """The threshold value to apply for the isosurface render method."""
        return self._threshold

    @threshold.setter
    def threshold(self, value):
        # Fix for #1399, should be fixed in the VisPy threshold setter
        self._threshold = float(value)
        self.shared_program['u_threshold'] = self._threshold
        self.update()

    @property
    def attenuation(self):
        """The attenuation value to apply for the attenuated mip render method."""
        return self._attenuation

    @attenuation.setter
    def attenuation(self, value):
        # Fix for #1399, should be fixed in the VisPy threshold setter
        self._attenuation = float(value)
        self.shared_program['u_attenuation'] = self._attenuation
        self.update()

    @property
    def shader(self):
        return self._shader

    @shader.setter
    def shader(self, value):
        """Set the base shader used for volume rendering"""
        if value not in ('volume', 'plane'):
            raise ValueError('value not in volume, plane')
        self._shader = value
        self.shared_program.frag = self.frag_dict[self.method]
        self.update()

    @property
    def frag_dict(self):
        """dict of fragment shaders"""
        if self.shader == 'volume':
            return frag_dict_volume
        elif self.shader == 'plane':
            return frag_dict_plane

    @property
    def method(self):
        """The render method to use

        Current options are:

            * translucent: voxel colors are blended along the view ray until
              the result is opaque.
            * mip: maxiumum intensity projection. Cast a ray and display the
              maximum value that was encountered.
            * additive: voxel colors are added along the view ray until
              the result is saturated.
            * iso: isosurface. Cast a ray until a certain threshold is
              encountered. At that location, lighning calculations are
              performed to give the visual appearance of a surface.
        """
        return self._method

    @method.setter
    def method(self, method):
        # Check and save
        known_methods = list(self.frag_dict.keys())
        if method not in known_methods:
            raise ValueError(
                'Volume render method should be in %r, not %r'
                % (known_methods, method)
            )
        self._method = method
        # Get rid of specific variables - they may become invalid
        if 'u_threshold' in self.shared_program:
            self.shared_program['u_threshold'] = None

        self.shared_program.frag = self.frag_dict[method]
        self.shared_program.frag['sampler_type'] = self._tex.glsl_sampler_type
        self.shared_program.frag['sample'] = self._tex.glsl_sample
        self.shared_program.frag['cmap'] = Function(self._cmap.glsl_map)
        self.shared_program['texture2D_LUT'] = (
            self.cmap.texture_lut()
            if (hasattr(self.cmap, 'texture_lut'))
            else None
        )
        self.update()
