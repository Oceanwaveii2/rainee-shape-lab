precision highp float;
precision highp int;
uniform vec3 raineeGrowthCenter_3;

uniform vec3 raineeGrowthRadii_4;

uniform float raineeGrowthFactor_5;

struct ExtSplats {
  usampler2DArray textureArray1;
  usampler2DArray textureArray2;
  int numSplats;
};

uniform ExtSplats extSplats_8;

uniform usampler2D lodIndices_10;

uniform int value_11;

uniform bool value_12;

uniform int value_13;

struct Gsplat {
  vec3 center;
  uint flags;
  vec3 scales;
  int index;
  vec4 quaternion;
  vec4 rgba;
};
const uint GSPLAT_FLAG_ACTIVE = 1u << 0u;

bool isGsplatActive(uint flags) {
  return (flags & GSPLAT_FLAG_ACTIVE) != 0u;
}

void readExtArrays(usampler2DArray texture1, usampler2DArray texture2, int numSplats, int index, out Gsplat gsplat) {
  gsplat.flags = 0u;
  if ((index >= 0) && (index < numSplats)) {
    ivec3 coord = splatTexCoord(index);
    uvec4 packed1 = texelFetch(texture1, coord, 0);
    uvec4 packed2 = texelFetch(texture2, coord, 0);
    unpackSplatExt(packed1, packed2, gsplat.center, gsplat.scales, gsplat.quaternion, gsplat.rgba);
    gsplat.flags = all(equal(gsplat.scales, vec3(0.0, 0.0, 0.0))) ? 0u : GSPLAT_FLAG_ACTIVE;
    gsplat.index = index;
  }
}

struct CovSplat {
  vec3 center;
  uint flags;
  vec4 rgba;
  vec3 xxyyzz;
  int index;
  vec3 xyxzyz;
};

bool isCovSplatActive(uint flags) {
  return (flags & GSPLAT_FLAG_ACTIVE) != 0u;
}


void raineeCompactGrowth(inout CovSplat splat, vec3 centre, vec3 radii, float growth) {
  if (!isCovSplatActive(splat.flags) || growth == 1.0) return;
  if (growth < 1.0 || growth > 2.25 || isnan(growth) || isinf(growth)
      || any(lessThan(radii, vec3(0.0001))) || any(isnan(radii)) || any(isinf(radii))) return;
  vec3 d = splat.center - centre;
  vec3 normalized = d / radii;
  float q = dot(normalized, normalized);
  if (q >= 1.0 || isnan(q) || isinf(q)) return;
  float k = growth - 1.0;
  float u = 1.0 - q;
  float w = u*u*u;
  vec3 gradient = -6.0*u*u*d/(radii*radii);
  mat3 J = mat3(1.0);
  for (int column=0; column<3; ++column)
    for (int row=0; row<3; ++row)
      J[column][row] += k * ((column == row ? w : 0.0) + d[row]*gradient[column]);
  float detJ = determinant(J);
  if (detJ <= 0.05 || isnan(detJ) || isinf(detJ)) return;
  mat3 covariance = mat3(
    splat.xxyyzz.x, splat.xyxzyz.x, splat.xyxzyz.y,
    splat.xyxzyz.x, splat.xxyyzz.y, splat.xyxzyz.z,
    splat.xyxzyz.y, splat.xyxzyz.z, splat.xxyyzz.z);
  covariance = J * covariance * transpose(J);
  if (any(isnan(covariance[0])) || any(isnan(covariance[1])) || any(isnan(covariance[2]))
      || any(isinf(covariance[0])) || any(isinf(covariance[1])) || any(isinf(covariance[2]))) return;
  splat.center += k*w*d;
  splat.xxyyzz = vec3(covariance[0][0], covariance[1][1], covariance[2][2]);
  splat.xyxzyz = vec3(covariance[0][1], covariance[0][2], covariance[1][2]);
}


uniform mat3 value_14;

uniform vec3 value_15;

uniform vec4 value_17;
out vec4 color;
void main(){
 CovSplat result;
 // DynoBlock(0) => (result)
 {
  // DynoVec3() => (raineeGrowthCenter_3)
  
  // DynoVec3() => (raineeGrowthRadii_4)
  
  // DynoFloat() => (raineeGrowthFactor_5)
  
  // DynoExtSplats() => (extSplats_8)
  
  // DynoUsampler2D() => (lodIndices_10)
  
  // DynoInt() => (value_11)
  
  // DynoBool() => (value_12)
  
  // DynoInt() => (value_13)
  
  // Dyno(lodIndices_10, 0, value_11, value_12, value_13) => (index_9)
  int index_9;
  {
   int index = 0;
   if (value_13 < 0) {
     if (index >= value_11) {
       return;
     }
     if (value_12) {
       ivec2 lodIndexCoord = ivec2((index >> 2) & 4095, index >> 14);
       uint splatIndex = texelFetch(lodIndices_10, lodIndexCoord, 0)[index & 3];
       index_9 = int(splatIndex);
     } else {
       index_9 = index;
     }
   } else {
     int start = value_13 << 16;
     if (index >= 65536) {
       return;
     }
     index_9 = start + index;
   }
  }
  
  // ReadExtSplat(extSplats_8, index_9) => (gsplat_7)
  Gsplat gsplat_7;
  {
   readExtArrays(extSplats_8.textureArray1, extSplats_8.textureArray2, extSplats_8.numSplats, index_9, gsplat_7);
  }
  
  // GsplatToCovSplat(gsplat_7) => (covsplat_6)
  CovSplat covsplat_6;
  {
   covsplat_6.flags = 0u;
   if (isGsplatActive(gsplat_7.flags)) {
     covsplat_6.flags = gsplat_7.flags;
     covsplat_6.index = gsplat_7.index;
     covsplat_6.rgba = gsplat_7.rgba;
     covsplat_6.center = gsplat_7.center;
     mat3 m = scaleQuaternionToMatrix(gsplat_7.scales, gsplat_7.quaternion);
     m = m * transpose(m);
     covsplat_6.xxyyzz = vec3(m[0][0], m[1][1], m[2][2]);
     covsplat_6.xyxzyz = vec3(m[0][1], m[0][2], m[1][2]);
   }
  }
  
  // Dyno(raineeGrowthCenter_3, raineeGrowthRadii_4, raineeGrowthFactor_5, covsplat_6) => (covsplat_2)
  CovSplat covsplat_2;
  {
   covsplat_2 = covsplat_6;
   raineeCompactGrowth(covsplat_2, raineeGrowthCenter_3, raineeGrowthRadii_4, raineeGrowthFactor_5);
  }
  
  // DynoMat3() => (value_14)
  
  // DynoVec3() => (value_15)
  
  // Dyno(covsplat_2, value_14, value_15) => (covsplat_1)
  CovSplat covsplat_1;
  {
   covsplat_1.flags = 0u;
   if (isCovSplatActive(covsplat_2.flags)) {
     covsplat_1.flags = covsplat_2.flags;
     covsplat_1.index = covsplat_2.index;
     covsplat_1.rgba = covsplat_2.rgba;
   
     covsplat_1.center = value_14 * covsplat_2.center + value_15;
   
     mat3 cov = mat3(
       covsplat_2.xxyyzz.x, covsplat_2.xyxzyz.x, covsplat_2.xyxzyz.y,
       covsplat_2.xyxzyz.x, covsplat_2.xxyyzz.y, covsplat_2.xyxzyz.z,
       covsplat_2.xyxzyz.y, covsplat_2.xyxzyz.z, covsplat_2.xxyyzz.z
     );
     cov = value_14 * cov * transpose(value_14);
     covsplat_1.xxyyzz = vec3(cov[0][0], cov[1][1], cov[2][2]);
     covsplat_1.xyxzyz = vec3(cov[0][1], cov[0][2], cov[1][2]);
   }
  }
  
  // DynoVec4() => (value_17)
  
  // SplitCovSplat(covsplat_1) => (rgba_18)
  vec4 rgba_18;
  {
   rgba_18 = covsplat_1.rgba;
  }
  
  // Mul(value_17, rgba_18) => (product_16)
  vec4 product_16;
  {
   product_16 = value_17 * rgba_18;
  }
  
  // CombineCovSplat(covsplat_1, product_16) => (result)
  {
   result.flags = covsplat_1.flags;
   result.index = covsplat_1.index;
   result.center = covsplat_1.center;
   result.rgba = product_16;
   result.xxyyzz = covsplat_1.xxyyzz;
   result.xyxzyz = covsplat_1.xyxzyz;
  }
 }
 color=result.rgba;
}