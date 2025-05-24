# Ridge Regression - TensorFlow.js

## 📁 Files
- `model.json` - Model architecture
- `*.bin` - Model weights  
- `demo.html` - Interactive web demo

## 🚀 Usage

### Method 1: Local Server
```bash
# Start a local server in this directory
python -m http.server 8000
# Open http://localhost:8000/demo.html
```

### Method 2: JavaScript Code
```javascript
// Load model
const model = await tf.loadLayersModel('./model.json');

// Make prediction
const input = tf.tensor2d([[/* your features */]]);
const prediction = model.predict(input);
const result = await prediction.data();
console.log('Prediction:', result[0]);
```

### Method 3: Web Integration
```html
<script src="https://cdn.jsdelivr.net/npm/@tensorflow/tfjs@latest"></script>
<script>
    async function predict(features) {
        const model = await tf.loadLayersModel('./model.json');
        const input = tf.tensor2d([features]);
        const prediction = model.predict(input);
        return await prediction.data();
    }
</script>
```

## 📊 Model Info
- **Conversion Type:** SavedModel
- **Input Shape:** Will be displayed in demo
- **Output:** Single numerical prediction

## 🔧 Requirements
- Modern web browser with JavaScript enabled
- TensorFlow.js library (loaded via CDN in demo)
