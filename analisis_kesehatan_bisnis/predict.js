import * as tf from '@tensorflow/tfjs';

async function loadModel() {
    const model = await tf.loadLayersModel('tfjs_model/model.json');
    const scalerParams = await fetch('scaler_params.json').then(r => r.json());
    const labelClasses = await fetch('label_classes.json').then(r => r.json());
    return { model, scalerParams, labelClasses };
}

function preprocessInput(data, scalerParams) {
    const inputTensor = tf.tensor2d([data]);
    
    const mean = tf.tensor1d(scalerParams.mean_);
    const scale = tf.tensor1d(scalerParams.scale_);
    
    const normalized = inputTensor.sub(mean).div(scale);
    return normalized;
}

// Make prediction
async function predictKondisiKeuangan(data) {
    const { model, scalerParams, labelClasses } = await loadModel();
    
    // Preprocess the input
    const preprocessedData = preprocessInput(data, scalerParams);
    
    // Make prediction
    const prediction = await model.predict(preprocessedData).array();
    
    // Get the predicted class
    const predictedClassIndex = prediction[0].indexOf(Math.max(...prediction[0]));
    const predictedClass = labelClasses[predictedClassIndex];
    
    return {
        predictedClass,
        probabilities: prediction[0]
    };
}

// Example usage
const sampleData = {
    pemasukan: 3000000,
    pengeluaran: 2950000,
    jumlah_transaksi: 12,
    jumlah_hari_rugi: 6,
    rasio_transaksi: 12 / (2950000 + 1),
    persen_pengeluaran: 2950000 / (3000000 + 2950000 + 1e-9)
};

// Convert sample data to array in the correct order
const inputData = [
    sampleData.pemasukan,
    sampleData.pengeluaran,
    sampleData.jumlah_transaksi,
    sampleData.jumlah_hari_rugi,
    sampleData.rasio_transaksi,
    sampleData.persen_pengeluaran
];

// Make prediction
predictKondisiKeuangan(inputData)
    .then(result => {
        console.log('Predicted class:', result.predictedClass);
        console.log('Probabilities:', result.probabilities);
    })
    .catch(error => {
        console.error('Error making prediction:', error);
    }); 