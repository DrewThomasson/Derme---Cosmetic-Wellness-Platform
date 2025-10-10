# Derme - Cosmetic Wellness Platform
Software Engineering Project

<p align="center">
  <img width="770" height="291" alt="Screenshot 2025-10-06 at 8 54 58 PM" src="https://github.com/user-attachments/assets/5bbf9243-58ee-4f15-96b6-def4d5461f4c" />
</p>

**Course:** Software Engineering Project - Fall 2025  
**Group:** Super Cool Guys (Group 8)

[![Hugging Face](https://img.shields.io/badge/Hugging%20Face-Demo-yellow?style=flat&logo=huggingface)](https://huggingface.co/spaces/drewThomasson/DermTest)
[![Free Google Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1TjPwaykftmQ6XpG7HKbmKlZyYlb65nLI?usp=sharing)
<a href="https://github.com/DrewThomasson/Derme---Cosmetic-Wellness-Platform">
  <img src="https://img.shields.io/badge/Platform-mac%20|%20linux%20|%20windows-lightgrey" alt="Platform">
</a>

---
> [!IMPORTANT]
> **For Informational Use Only. Not Medical Advice.**
> 
> This application is not a substitute for professional medical advice, diagnosis, or treatment. Always consult a qualified health provider with any questions regarding a medical condition. The developers assume no liability for the use of this software.
> 
> **In case of an emergency, call 911 immediately.**

## Table of Contents
- [Project Overview](#project-overview)
- [Problem Statement](#problem-statement)
- [Core System Goals](#core-system-goals)
- [Installation](#installation)
  - [Prerequisites](#prerequisites)
  - [Setup Steps](#setup-steps)
- [Demo](#demo)
- [Team Members](#team-members)

---

## Project Overview

Derme is a mobile application designed to help users with sensitive skin and allergies analyze ingredients in cosmetic products. By scanning products, users can identify potential allergens, track skin reactions, and receive personalized recommendations.

---

## Problem Statement

Consumers with sensitive skin and allergies face a significant challenge in identifying potential irritants within the complex ingredient lists of cosmetic and skincare products. This difficulty creates a barrier for individuals wishing to safely purchase new products and makes it hard to provide accurate information to dermatologists when trying to diagnose the source of an adverse reaction.

The process of tracking ingredients, cross-referencing them with known allergens, and correlating them to specific skin reactions is manually intensive and often unreliable. This leaves users feeling frustrated and disempowered, turning the proactive management of their skin health into a constant struggle. Derme aims to solve this by providing a centralized, intelligent platform to simplify ingredient analysis and allergy management.

---

## Core System Goals

Our goal is to build a system that can:
* **Scan Products:** Allow users to scan product barcodes or upload images of ingredient labels with AI-powered OCR.
* **Analyze Ingredients:** Cross-reference ingredients against a known allergen database and a user's personal allergy list using Google Gemini AI.
* **Smart Allergen Detection:** Identify allergens by their alternative names and synonyms using AI.
* **Track Symptoms:** Provide a journal for users to log skin reactions and connect them to specific products.
* **Provide Alerts:** Notify users about potential flare-ups based on environmental data (pollen, air quality).
* **Offer Emergency Support:** Integrate features to contact emergency services and share allergy information.

---

## 🚀 New: AI-Powered Analysis with Google Gemini

The application now integrates **Google Gemini AI** for enhanced allergen detection:

- **🔍 Smart OCR**: Better ingredient extraction from product photos
- **🧠 Intelligent Analysis**: Identifies allergens by alternative names and synonyms
- **📚 Detailed Information**: Get comprehensive details about any ingredient
- **⚡ Real-time Insights**: AI-powered explanations for detected allergens

**See [CONFIG_README.md](CONFIG_README.md) for setup instructions.**

The app works perfectly without a Gemini API key - it falls back to traditional OCR and database lookup.

---

## Installation

### Quick Start with Docker (Recommended)

The easiest way to run Derme is using Docker:

```bash
# Clone the repository
git clone https://github.com/DrewThomasson/Derme---Cosmetic-Wellness-Platform.git
cd Derme---Cosmetic-Wellness-Platform

# Start with Docker Compose
docker compose up -d

# Access at http://localhost:7860
```

**See [DOCKER_README.md](DOCKER_README.md) for complete Docker setup and configuration.**

### Manual Installation

#### Prerequisites

* Miniconda or Anaconda installed on your system
* Python 3.8 or higher
* Git
* Tesseract OCR (for image text extraction)

#### Setup Steps

**Clone the repository:**
```bash
git clone https://github.com/DrewThomasson/Derme---Cosmetic-Wellness-Platform.git
cd Derme---Cosmetic-Wellness-Platform
```

**Create a conda environment:**
```bash
conda create -n derme python=3.9
conda activate derme
```

**Install dependencies:**
```bash
pip install -r requirements.txt
```

**Configure the application (optional):**

For AI-powered features, set up Google Gemini:
```bash
# Copy the example configuration
cp .env.example .env

# Edit .env and add your Gemini API key
# Get your key from: https://makersuite.google.com/app/apikey
```

See [CONFIG_README.md](CONFIG_README.md) for detailed configuration options.

**Run the application:**
```bash
python app.py
```

---

## Demo

Try out our live demo on Hugging Face Spaces:  
[![Hugging Face](https://img.shields.io/badge/Hugging%20Face-Demo-yellow?style=flat&logo=huggingface)](https://huggingface.co/spaces/drewThomasson/DermTest)
[![Free Google Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1TjPwaykftmQ6XpG7HKbmKlZyYlb65nLI?usp=sharing)

---

## Team Members

* Naol Seyum
* Sansca Raut
* Amna Yousuf (Coordinator)
* Trenton Ellis (Coordinator)
* Brij Chovatiya
* Drew Thomasson
