from bib import choose_cite_names


def main():
    import numpy as np
    np.set_printoptions(suppress=True, precision=3)
    test_titles = [
        "scroll efficient selectivity and backup operators in monte-carlo tree search",
        "mastering the game of go with deep neural networks and tree search",
        "a universal music translation network",
        "sneakysnake: a fast and accurate universal genome pre-alignment filter for cpus, gpus, and fpgas",
        "shouji: a fast and efficient pre-alignment filter for sequence alignment",
        "scroll digital video stabilization and rolling shutter correction using gyroscopes",
        "an improved illumination model for shaded display",
        "gigavoxels: ray-guided streaming for efficient and detailed voxel rendering",
        "continuous shading of curved surfaces",
        "illumination for computer generated pictures",
        "kinectfusion: real-time 3d reconstruction and interaction using a moving depth camera",
        "3-sweep: extracting editable objects from a single photo",
        "deep photo style transfer",
        "light propagation volumes in cryengine 3",
        "interactive horizon mapping: shadows for bump-mapped surfaces",
        "interior mapping: a new technique for rendering realistic buildings",
        "procedural modeling of buildings",
        "shape grammars and the generative specification of painting and sculpture",
    ]
    print(choose_cite_names(test_titles))


if __name__ == '__main__':
    main()
