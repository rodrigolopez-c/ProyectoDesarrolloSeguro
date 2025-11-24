const db = require('./db-sqlite');

const sampleProducts = [
  { name: 'Laptop Dell XPS 13', price: 1299.99, category: 'Electronics', stock: 15 },
  { name: 'iPhone 15 Pro', price: 999.99, category: 'Electronics', stock: 30 },
  { name: 'Samsung Galaxy S24', price: 899.99, category: 'Electronics', stock: 25 },
  { name: 'MacBook Pro M3', price: 2499.99, category: 'Electronics', stock: 10 },
  { name: 'Sony WH-1000XM5 Headphones', price: 399.99, category: 'Audio', stock: 50 },
  { name: 'iPad Air', price: 599.99, category: 'Electronics', stock: 20 },
  { name: 'Nintendo Switch OLED', price: 349.99, category: 'Gaming', stock: 40 },
  { name: 'PlayStation 5', price: 499.99, category: 'Gaming', stock: 12 },
  { name: 'Xbox Series X', price: 499.99, category: 'Gaming', stock: 18 },
  { name: 'Apple Watch Series 9', price: 429.99, category: 'Wearables', stock: 35 },
  { name: 'Kindle Paperwhite', price: 139.99, category: 'Electronics', stock: 60 },
  { name: 'GoPro Hero 12', price: 399.99, category: 'Cameras', stock: 22 },
  { name: 'DJI Mini 3 Drone', price: 759.99, category: 'Cameras', stock: 8 },
  { name: 'Bose QuietComfort Earbuds', price: 299.99, category: 'Audio', stock: 45 },
  { name: 'LG OLED TV 55"', price: 1799.99, category: 'Electronics', stock: 7 },
  { name: 'Samsung 4K Monitor', price: 399.99, category: 'Electronics', stock: 28 },
  { name: 'Logitech MX Master 3S Mouse', price: 99.99, category: 'Accessories', stock: 100 },
  { name: 'Mechanical Keyboard RGB', price: 149.99, category: 'Accessories', stock: 55 },
  { name: 'Webcam Logitech C920', price: 79.99, category: 'Accessories', stock: 65 },
  { name: 'External SSD 1TB', price: 129.99, category: 'Storage', stock: 70 },
  { name: 'Portable Charger 20000mAh', price: 49.99, category: 'Accessories', stock: 120 },
  { name: 'USB-C Hub Multiport', price: 59.99, category: 'Accessories', stock: 90 },
  { name: 'Ring Video Doorbell', price: 99.99, category: 'Smart Home', stock: 42 },
  { name: 'Amazon Echo Dot', price: 49.99, category: 'Smart Home', stock: 150 },
  { name: 'Philips Hue Starter Kit', price: 199.99, category: 'Smart Home', stock: 33 }
];

async function initializeDatabase() {
  try {
    console.log('Inicializando base de datos SQLite...');
    
    console.log('Eliminando tabla anterior si existe...');
    await db.runAsync('DROP TABLE IF EXISTS products');
    
    console.log('Creando tabla products...');
    await db.runAsync(`
      CREATE TABLE products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        price REAL NOT NULL,
        category TEXT NOT NULL,
        stock INTEGER NOT NULL DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
      )
    `);
    
    console.log('Tabla creada exitosamente.');
    
    console.log('Insertando productos de ejemplo...');
    
    const insertQuery = `INSERT INTO products (name, price, category, stock) VALUES (?, ?, ?, ?)`;
    
    for (const product of sampleProducts) {
      await db.runAsync(insertQuery, [
        product.name,
        product.price,
        product.category,
        product.stock
      ]);
    }
    
    console.log(`${sampleProducts.length} productos insertados exitosamente.`);
    
    const result = await db.queryAsync('SELECT COUNT(*) as count FROM products');
    console.log(`Total de productos en la base de datos: ${result.rows[0].count}`);
    
    const sample = await db.queryAsync('SELECT * FROM products LIMIT 5');
    console.log('\nPrimeros 5 productos:');
    console.table(sample.rows);
    
    console.log('\n✓ Base de datos poblada correctamente.');
    
  } catch (error) {
    console.error('Error al inicializar la base de datos:', error);
    throw error;
  } finally {
    db.close();
  }
}

initializeDatabase()
  .then(() => {
    console.log('\nScript completado. Puedes iniciar el servidor con: npm start');
    process.exit(0);
  })
  .catch((error) => {
    console.error('\nError fatal:', error.message);
    process.exit(1);
  });