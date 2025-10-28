# Derme - Cosmetic Wellness Platform

<img width="1344" height="768" alt="Gemini_Generated_Image_gdr0wpgdr0wpgdr0" src="https://github.com/user-attachments/assets/78ab918e-2068-4ebf-abe2-f5c330cf94ba" />


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
One of our team members, Drew Thomasson, frequently experiences skin reactions and has spent considerable time and money consulting multiple dermatologists to identify the causes. This challenge inspired our team to develop a solution that simplifies tracking symptoms and identifying potential skin irritants for individuals facing similar issues.

Consumers with sensitive skin or allergies struggle to identify harmful ingredients within the often complex and technical ingredient lists of cosmetic and skincare products. This difficulty not only creates anxiety when purchasing new products but also makes it challenging to provide dermatologists with accurate information for diagnosing adverse skin reactions.

Currently, tracking ingredients, cross-referencing them with known allergens, and linking them to specific skin symptoms is a tedious and error-prone process. As a result, users often feel frustrated and powerless in managing their skin health.

**Derme** aims to address this problem by providing a centralized, intelligent platform that streamlines ingredient analysis, symptom tracking, and allergy management—empowering users to make safer and more informed skincare decisions.


---

## Core System Goals

Our goal is to build a system that can:
* **Scan Products:** Allow users to scan product barcodes or upload images of ingredient labels.
* **Analyze Ingredients:** Cross-reference ingredients against a comprehensive allergen database (496 known contact dermatitis allergens) and a user's personal allergy list.
* **Track Symptoms:** Provide a journal for users to log skin reactions and connect them to specific products.
* **Provide Alerts:** Notify users about potential flare-ups based on environmental data (pollen, air quality).
* **Offer Emergency Support:** Integrate features to contact emergency services and share allergy information.

---

## Features

### Comprehensive Allergen Database

Derme includes a comprehensive database of **496 known allergens** that commonly cause contact dermatitis, sourced from the **[Contact Dermatitis Institute]**(https://www.contactdermatitisinstitute.com). 

The database includes:
- **14,000+ ingredient synonyms** for accurate matching across different naming conventions
- Detailed information about where each allergen is commonly found
- Product categories that may contain the allergen
- Clinical notes for medical professionals
- Links to additional information

This enables the app to detect potential allergens in cosmetic products even when they're listed under alternative names, chemical names, or trade names.

---

## Installation

### Prerequisites

* Miniconda or Anaconda installed on your system
* Python 3.8 or higher
* Git

### Setup Steps

**Clone the repository:**
```bash
git clone https://github.com/DrewThomasson/Derme---Cosmetic-Wellness-Platform.git
cd Derme---Cosmetic-Wellness-Platform
```

**Create a conda environment:**
```bash
conda create -n derme python=3.10.18
conda activate derme
```

**Install dependencies:**
```bash
pip install -r requirements.txt
```

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
* Amna Yousuf 
* Trenton Ellis 
* Brij Chovatiya
* Drew Thomasson
