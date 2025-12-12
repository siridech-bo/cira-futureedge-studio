# 🚀 CiRA FutureEdge Studio

**AI-Powered Edge ML Platform for Anomaly Detection & Classification**

---

## 📖 Overview

**CiRA FutureEdge Studio** is a comprehensive desktop application for building, training, and deploying machine learning models for edge devices. It combines cutting-edge AI techniques with an intuitive UI to enable rapid development of both **anomaly detection** and **multi-class classification** models from sensor data.

### ✨ Key Features

- 🎯 **Dual Mode Operation**: Switch seamlessly between Anomaly Detection and Classification
- 📊 **Multiple Data Sources**: CSV, Edge Impulse (JSON/CBOR), Database, REST API, Streaming
- 🪟 **Advanced Windowing**: Time-series segmentation with label preservation via majority voting
- 🔍 **Intelligent Feature Extraction**: TSFresh + Custom DSP features (40+ features)
- 🤖 **LLM-Powered Feature Selection**: Local Llama 3.2 integration for optimal feature selection
- 📈 **10 Anomaly Detection Algorithms**: Isolation Forest, LOF, One-Class SVM, and more (PyOD)
- 🎓 **8 Classification Algorithms**: Random Forest, Gradient Boosting, SVM, MLP, KNN, and more
- 📉 **Rich Visualizations**: Confusion matrices, feature importance, sensor plots
- 💾 **Project Management**: Save/load complete ML pipelines
- 🎨 **Modern UI**: CustomTkinter with light/dark theme support

## 🚀 Quick Start

### Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run: `python main.py`

## 📚 Usage

See [SPRINT5_COMPLETE.md](SPRINT5_COMPLETE.md) for detailed workflow examples.

## 🎯 Algorithms

**Anomaly Detection (PyOD):** Isolation Forest, LOF, One-Class SVM, HBOS, KNN, and more

**Classification (Scikit-learn):** Random Forest, Gradient Boosting, SVM, MLP, KNN, Decision Tree, Naive Bayes, Logistic Regression

## 📦 Dependencies

- customtkinter, pandas, numpy, scikit-learn, pyod, tsfresh, matplotlib, seaborn

See requirements.txt for full list.

## 📄 License

MIT License

---

**Built with ❤️ for Edge ML Development**
