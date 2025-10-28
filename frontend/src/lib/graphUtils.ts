/**
* Converts a hex color string to a normalized RGBA Float32Array
* @param hex - Hex color string (e.g., "#ff0000" or "#ff0000ff")
* @returns Float32Array [r, g, b, a] with values 0-1
*/
export function hexToRGBA(hex: string): Float32Array {
    const r = parseInt(hex.slice(1, 3), 16) / 255;
    const g = parseInt(hex.slice(3, 5), 16) / 255;
    const b = parseInt(hex.slice(5, 7), 16) / 255;
    const a = hex.length === 9 ? parseInt(hex.slice(7, 9), 16) / 255 : 1.0;
    return new Float32Array([r, g, b, a]);
}

/**
* Creates a color array with uniform color for all points
* @param numPoints - Number of points
* @param color - RGBA color as Float32Array [r, g, b, a]
* @returns Float32Array ready for setPointColors
*/
export function createUniformColorArray(numPoints: number, color: Float32Array): Float32Array {
    const array = new Float32Array(numPoints * 4);
    for (let i = 0; i < numPoints; i++) {
        array[i * 4] = color[0];
        array[i * 4 + 1] = color[1];
        array[i * 4 + 2] = color[2];
        array[i * 4 + 3] = color[3];
    }
    return array;
}

/**
* Creates a size array with uniform size for all points
* @param numPoints - Number of points
* @param size - Size value for all points
* @returns Float32Array ready for setPointSizes
*/
export function createUniformSizeArray(numPoints: number, size: number): Float32Array {
    const array = new Float32Array(numPoints);
    array.fill(size);
    return array;
}

/**
* Applies a color to specific point indices in an existing color array
* @param existingColors - Current color array (will be cloned)
* @param indices - Point indices to color
* @param color - RGBA color as Float32Array [r, g, b, a]
* @returns New Float32Array with updated colors
*/
export function applyColorToIndices(
    existingColors: Float32Array,
    indices: number[],
    color: Float32Array
): Float32Array {
    const newColors = existingColors.slice();
    for (const idx of indices) {
        const offset = idx * 4;
        newColors[offset] = color[0];
        newColors[offset + 1] = color[1];
        newColors[offset + 2] = color[2];
        newColors[offset + 3] = color[3];
    }
    return newColors;
}