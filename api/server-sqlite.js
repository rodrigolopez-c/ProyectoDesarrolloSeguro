const express = require('express');
const fs = require('fs');
const path = require('path');
const db = require('./db-sqlite');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());
app.use(express.urlencoded({ extended: true }));

const LOG_FILE = path.join(__dirname, 'queries.log');

function logQuery(req, query) {
  const timestamp = new Date().toISOString();
  const ip = req.ip || req.connection.remoteAddress;
  const endpoint = req.originalUrl;
  const searchTerm = req.query.name || '';
  
  const logEntry = `[${timestamp}] IP: ${ip} | Endpoint: ${endpoint} | Search: ${searchTerm} | Query: ${query}\n`;
  
  fs.appendFile(LOG_FILE, logEntry, (err) => {
    if (err) {
      console.error('Error al escribir en el log:', err);
    }
  });
}

app.get('/api/products/search', async (req, res) => {
  const searchTerm = req.query.name || '';
  
  try {

    const query = `SELECT * FROM products WHERE name LIKE '%${searchTerm}%'`;
    
    logQuery(req, query);
    
    const result = await db.queryAsync(query);
    
    res.json({
      success: true,
      count: result.rows.length,
      data: result.rows
    });
    
  } catch (error) {
    console.error('Error en la búsqueda:', error);
    
    res.status(500).json({
      success: false,
      message: 'Error en la consulta',
      error: error.message
    });
  }
});

app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

app.get('/api/products', async (req, res) => {
  try {
    const result = await db.queryAsync('SELECT * FROM products ORDER BY id');
    res.json({
      success: true,
      count: result.rows.length,
      data: result.rows
    });
  } catch (error) {
    console.error('Error al obtener productos:', error);
    res.status(500).json({
      success: false,
      message: 'Error al obtener productos',
      error: error.message
    });
  }
});

app.get('/', (req, res) => {
  res.json({
    message: 'API de búsqueda de productos',
    endpoints: {
      search: '/api/products/search?name=<término>',
      all: '/api/products',
      health: '/health'
    }
  });
});

app.listen(PORT, () => {
  console.log(`Servidor corriendo en http://localhost:${PORT}`);
  console.log(`Endpoint de búsqueda: http://localhost:${PORT}/api/products/search?name=laptop`);
  console.log(`Log de consultas: ${LOG_FILE}`);
});