#  Compiler Optimization Toolkit

A robust, lightweight static analysis and code optimization toolkit built in Python. This tool parses Three-Address Code (TAC), executes core compiler optimization passes—including **Constant Propagation & Folding** and **Loop Invariant Code Motion (LICM)**—and generates visual **Control Flow Graphs (CFGs)**.

---

##  Key Features

* **Custom TAC Parser:** Reads and tokenizes raw intermediate representation (IR) files, stripping comments and validating instructions.
* **Constant Propagation & Folding:** Evaluates constant expressions at compile-time and propagates known values across instructions to eliminate redundant runtime calculations.
* **Loop Invariant Code Motion (LICM):** Automatically detects loop-independent calculations and hoists them outside loop headers to minimize iteration overhead.
* **Control Flow Graph (CFG) Generator:** Partitions instruction blocks and renders visual directed graphs using Graphviz (`.png` output).
* **Command-Line Interface (CLI):** Provides flexible command-line arguments to toggle optimization passes and graph generation dynamically.

---

##  Tech Stack

* **Language:** Python 3.x
* **Graph Rendering:** Graphviz
* **Architecture:** Modular compiler pipeline design (Parser ➔ Optimizer ➔ CFG Renderer)

---

# Requirements for Compiler Optimization Toolkit

graphviz>=0.20.1
##  Project Structure

```text
compiler_optimizer/
│
├── optimizer.py         # Core engine: parser, optimization passes, CLI, and CFG generator
├── test_code.tac        # Sample TAC input file for testing
├── requirements.txt     # Project dependencies
└── README.md            # Documentation