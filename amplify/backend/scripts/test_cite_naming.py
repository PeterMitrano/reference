from bib import choose_cite_names


def main():
    import numpy as np
    np.set_printoptions(suppress=True, precision=3)
    test_titles = [
        "3-sweep: extracting editable objects from a single photo",
        "a universal music translation network",
        "an improved illumination model for shaded display",
        "continuous shading of curved surfaces",
        "deep photo style transfer",
        "gigavoxels: ray-guided streaming for efficient and detailed voxel rendering",
        "illumination for computer generated pictures",
        "interactive horizon mapping: shadows for bump-mapped surfaces",
        "interior mapping: a new technique for rendering realistic buildings",
        "kinectfusion: real-time 3d reconstruction and interaction using a moving depth camera",
        "light propagation volumes in cryengine 3",
        "mastering the game of go with deep neural networks and tree search",
        "procedural modeling of buildings",
        "scroll digital video stabilization and rolling shutter correction using gyroscopes",
        "scroll efficient selectivity and backup operators in monte-carlo tree search",
        "shape grammars and the generative specification of painting and sculpture",
        "shouji: a fast and efficient pre-alignment filter for sequence alignment",
        "sneakysnake: a fast and accurate universal genome pre-alignment filter for cpus, gpus, and fpgas",
        '3D Neural Scene Representations For Visuomotor Control',
        'A Farewell To The Bias-Variance Tradeoff? An Overview Of The Theory Of Overparameterized Machine Learning',
        'A Novel Method For Developing Robotics Via Artificial Intelligence And Internet Of Things',
        'A Review Of Robot Learning For Manipulation: Challenges, Representations, And Algorithms',
        'A Survey On Semi-Supervised Learning',
        'Algorithms For Quantum Computation: Discrete Logarithms And Factoring',
        'An Empirical Investigation Of Catastrophic Forgeting In Gradient-Based Neural Networks',
        'Approximately Optimal Monitoring Of Plan Preconditions',
        'Belief Regulated Dual Propagation Nets For Learning Action Effects On Groups Of Articulated Objects',
        'Causal Reasoning In Simulation For Structure And Transfer Learning Of Robot Manipulation Policies',
        'Challenges And Outlook In Robotic Manipulation Of Deformable Objects',
        'Cost-Effective Training Of Deep Cnns With Active Model Adaptation',
        'Detect, Reject, Correct: Crossmodal Compensation Of Corrupted Sensors',
        'Discovering Generalizable Skills Via Automated Generation Of Diverse Tasks',
        'Domain Adaptation From Multiple Sources Via Auxiliary Classifiers',
        'Embracing Change: Continual Learning In Deep Neural Networks',
        'Examining The Correlation Of The Level Of Wage Inequality With Labor Market Institutions',
        'Futuremapping: The Computational Structure Of Spatial Ai Systems',
        'Latent Skill Planning For Exploration And Transfer',
        'Learning Transferable Features With Deep Adaptation Networks',
        'Meld: Meta-Reinforcement Learning From Images Via Latent State Models',
        'Motion Planner Augmented Reinforcement Learning For Robot Manipulation In Obstructed Environments',
        'Object And Relation Centric Representations For Push Effect Prediction',
        'One-Shot Learning Of Manipulation Skills With Online Dynamics Adaptation And Neural Network Priors',
        'Panoramic Learning With A Standardized Machine Learning Formalism',
        'Perspectives Article: Income Inequality, Health, And Household Welfare',
        'Posterior Sampling For Anytime Motion Planning On Graphs With Expensive-To-Evaluate Edges',
        'Task-Driven Out-Of-Distribution Detection With Statistical Guarantees For Robot Learning',
        'Technological Unemployment And Human Disenhancement', 'Meta-Learning In Neural Networks: A Survey',
        'Who Perceived Automation As A Threat To Their Jobs In Metro Atlanta: Results From The 2019 Metro Atlanta Speaks Survey',
    ]
    print(choose_cite_names(test_titles))


if __name__ == '__main__':
    main()
