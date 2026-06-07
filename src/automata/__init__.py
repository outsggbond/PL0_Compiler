# src/automata/__init__.py
"""Automata package: Regex → NFA → DFA → MinDFA pipeline.

Contains:
- nfa.py              : NFA class with epsilon-closure + Thompson construction helpers
- regex_to_nfa.py     : Regex parser → NFA via Thompson construction
- dfa.py              : DFA class + subset construction (NFA → DFA)
- dfa_minimizer.py    : Hopcroft DFA minimization algorithm
- automata_visualizer.py : Visualization utilities for NFA/DFA/MinDFA
"""
