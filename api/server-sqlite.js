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

function logQuery(req, query, method = 'GET') {
  const timestamp = new Date().toISOString();
  const ip = req.ip || req.connection.remoteAddress;
  const endpoint = req.originalUrl;
  const body = method !== 'GET' ? JSON.stringify(req.body) : 'N/A';
  
  const logEntry = `[${timestamp}] Method: ${method} | IP: ${ip} | Endpoint: ${endpoint} | Body: ${body} | Query: ${query}\n`;
  
  fs.appendFile(LOG_FILE, logEntry, (err) => {
    if (err) {
      console.error('Error al escribir en el log:', err);
    }
  });
}

app.get('/api/products', async (req, res) => {
  try {
    const query = 'SELECT * FROM products ORDER BY id';
    logQuery(req, query, 'GET');
    
    const result = await db.queryAsync(query);
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

app.get('/api/products/search', async (req, res) => {
  const searchTerm = req.query.name || '';
  
  try {
    const query = `SELECT * FROM products WHERE name LIKE '%${searchTerm}%'`;
    logQuery(req, query, 'GET');
    
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
      error: error.message,
      stack: error.stack
    });
  }
});

app.get('/api/products/:id', async (req, res) => {
  const productId = req.params.id;
  
  try {
    const query = `SELECT * FROM products WHERE id = ${productId}`;
    logQuery(req, query, 'GET');
    
    const result = await db.queryAsync(query);
    
    if (result.rows.length === 0) {
      return res.status(404).json({
        success: false,
        message: 'Producto no encontrado'
      });
    }
    
    res.json({
      success: true,
      data: result.rows[0]
    });
  } catch (error) {
    console.error('Error al obtener producto:', error);
    res.status(500).json({
      success: false,
      message: 'Error al obtener producto',
      error: error.message
    });
  }
});

app.get('/api/products/category/:category', async (req, res) => {
  const category = req.params.category;
  
  try {
    const query = `SELECT * FROM products WHERE category = '${category}'`;
    logQuery(req, query, 'GET');
    
    const result = await db.queryAsync(query);
    res.json({
      success: true,
      count: result.rows.length,
      data: result.rows
    });
  } catch (error) {
    console.error('Error al filtrar por categoría:', error);
    res.status(500).json({
      success: false,
      message: 'Error al filtrar',
      error: error.message
    });
  }
});

app.post('/api/products', async (req, res) => {
  const { name, price, category, stock } = req.body;
  
  try {
    const query = `INSERT INTO products (name, price, category, stock) VALUES ('${name}', ${price}, '${category}', ${stock})`;
    logQuery(req, query, 'POST');
    
    const result = await db.runAsync(query);
    
    res.status(201).json({
      success: true,
      message: 'Producto creado exitosamente',
      data: {
        id: result.lastID,
        name,
        price,
        category,
        stock
      }
    });
  } catch (error) {
    console.error('Error al crear producto:', error);
    res.status(500).json({
      success: false,
      message: 'Error al crear producto',
      error: error.message,
      query: `INSERT INTO products (name, price, category, stock) VALUES ('${name}', ${price}, '${category}', ${stock})` // ← Expone la query
    });
  }
});

app.put('/api/products/:id', async (req, res) => {
  const productId = req.params.id;
  const { name, price, category, stock } = req.body;
  
  try {
    const query = `UPDATE products SET name = '${name}', price = ${price}, category = '${category}', stock = ${stock} WHERE id = ${productId}`;
    logQuery(req, query, 'PUT');
    
    const result = await db.runAsync(query);
    
    if (result.changes === 0) {
      return res.status(404).json({
        success: false,
        message: 'Producto no encontrado'
      });
    }
    
    res.json({
      success: true,
      message: 'Producto actualizado exitosamente',
      data: { id: productId, name, price, category, stock }
    });
  } catch (error) {
    console.error('Error al actualizar producto:', error);
    res.status(500).json({
      success: false,
      message: 'Error al actualizar producto',
      error: error.message
    });
  }
});

app.patch('/api/products/:id', async (req, res) => {
  const productId = req.params.id;
  const updates = req.body;
  
  const setClauses = Object.keys(updates).map(key => {
    const value = typeof updates[key] === 'string' ? `'${updates[key]}'` : updates[key];
    return `${key} = ${value}`;
  }).join(', ');
  
  try {
    const query = `UPDATE products SET ${setClauses} WHERE id = ${productId}`;
    logQuery(req, query, 'PATCH');
    
    const result = await db.runAsync(query);
    
    if (result.changes === 0) {
      return res.status(404).json({
        success: false,
        message: 'Producto no encontrado'
      });
    }
    
    res.json({
      success: true,
      message: 'Producto actualizado parcialmente',
      updated: updates
    });
  } catch (error) {
    console.error('Error al actualizar producto:', error);
    res.status(500).json({
      success: false,
      message: 'Error al actualizar',
      error: error.message
    });
  }
});

app.delete('/api/products/:id', async (req, res) => {
  const productId = req.params.id;
  
  try {
    const query = `DELETE FROM products WHERE id = ${productId}`;
    logQuery(req, query, 'DELETE');
    
    const result = await db.runAsync(query);
    
    if (result.changes === 0) {
      return res.status(404).json({
        success: false,
        message: 'Producto no encontrado'
      });
    }
    
    res.json({
      success: true,
      message: 'Producto eliminado exitosamente'
    });
  } catch (error) {
    console.error('Error al eliminar producto:', error);
    res.status(500).json({
      success: false,
      message: 'Error al eliminar producto',
      error: error.message
    });
  }
});

app.delete('/api/products/category/:category', async (req, res) => {
  const category = req.params.category;
  
  try {
    const query = `DELETE FROM products WHERE category = '${category}'`;
    logQuery(req, query, 'DELETE');
    
    const result = await db.runAsync(query);
    
    res.json({
      success: true,
      message: `${result.changes} producto(s) eliminado(s)`,
      deleted: result.changes
    });
  } catch (error) {
    console.error('Error al eliminar productos:', error);
    res.status(500).json({
      success: false,
      message: 'Error al eliminar',
      error: error.message
    });
  }
});

app.get('/api/products/sort/:field', async (req, res) => {
  const field = req.params.field;
  const order = req.query.order || 'ASC';
  
  try {
    const query = `SELECT * FROM products ORDER BY ${field} ${order}`;
    logQuery(req, query, 'GET');
    
    const result = await db.queryAsync(query);
    res.json({
      success: true,
      count: result.rows.length,
      data: result.rows
    });
  } catch (error) {
    console.error('Error al ordenar:', error);
    res.status(500).json({
      success: false,
      message: 'Error al ordenar',
      error: error.message
    });
  }
});

app.post('/api/products/advanced-search', async (req, res) => {
  const { name, minPrice, maxPrice, category } = req.body;
  
  let conditions = [];
  if (name) conditions.push(`name LIKE '%${name}%'`);
  if (minPrice) conditions.push(`price >= ${minPrice}`);
  if (maxPrice) conditions.push(`price <= ${maxPrice}`);
  if (category) conditions.push(`category = '${category}'`);
  
  const whereClause = conditions.length > 0 ? 'WHERE ' + conditions.join(' AND ') : '';
  
  try {
    const query = `SELECT * FROM products ${whereClause}`;
    logQuery(req, query, 'POST');
    
    const result = await db.queryAsync(query);
    res.json({
      success: true,
      count: result.rows.length,
      data: result.rows
    });
  } catch (error) {
    console.error('Error en búsqueda avanzada:', error);
    res.status(500).json({
      success: false,
      message: 'Error en la búsqueda',
      error: error.message
    });
  }
});

app.get('/health', (req, res) => {
  res.json({ 
    status: 'ok', 
    timestamp: new Date().toISOString(),
    database: 'SQLite',
    version: '1.0.0'
  });
});

app.get('/', (req, res) => {
  res.json({
    message: 'API REST CRUD - Sistema de Productos',
    version: '1.0.0',
    endpoints: {
      read: {
        all: 'GET /api/products',
        byId: 'GET /api/products/:id',
        search: 'GET /api/products/search?name=<término>',
        byCategory: 'GET /api/products/category/:category',
        sorted: 'GET /api/products/sort/:field?order=ASC|DESC'
      },
      create: {
        new: 'POST /api/products'
      },
      update: {
        full: 'PUT /api/products/:id',
        partial: 'PATCH /api/products/:id'
      },
      delete: {
        byId: 'DELETE /api/products/:id',
        byCategory: 'DELETE /api/products/category/:category'
      },
      advanced: {
        search: 'POST /api/products/advanced-search'
      },
      utility: {
        health: 'GET /health'
      }
    }
  });
});

app.listen(PORT, () => {
  console.log(`Servidor CRUD corriendo en http://localhost:${PORT}`);
  console.log(`Documentación: http://localhost:${PORT}/`);
  console.log(`Log de consultas: ${LOG_FILE}`);
  console.log('\nEndpoints disponibles:');
  console.log('  GET    /api/products                    - Listar todos');
  console.log('  GET    /api/products/:id                - Obtener por ID');
  console.log('  GET    /api/products/search?name=...    - Buscar');
  console.log('  POST   /api/products                    - Crear nuevo');
  console.log('  PUT    /api/products/:id                - Actualizar completo');
  console.log('  PATCH  /api/products/:id                - Actualizar parcial');
  console.log('  DELETE /api/products/:id                - Eliminar');
});