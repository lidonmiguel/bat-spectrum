# Bat Spectrum — Visual System

This document describes how acoustic features extracted from bat recordings are mapped into visual parameters for generative visualization.

## Current pipeline

WAV audio files  
→ pulse / event detection  
→ acoustic feature extraction  
→ CSV export  
→ TouchDesigner-ready visual data  
→ generative visualization

## Main export file

The main CSV for visual work is:

```text
data/exports/touchdesigner_pulses.csv