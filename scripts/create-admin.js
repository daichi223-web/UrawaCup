/**
 * 管理者ユーザー作成スクリプト (Node.js版)
 *
 * 使用方法:
 *   node scripts/create-admin.js
 */

const bcrypt = require('bcryptjs');
const Database = require('better-sqlite3');
const path = require('path');

// データベースパス
const dbPath = path.join(__dirname, '..', 'urawa_cup.db');

// 管理者情報
const admin = {
  username: 'admin',
  password: 'admin1234',
  display_name: 'システム管理者',
  role: 'admin'
};

async function main() {
  console.log('浦和カップ - 管理者作成スクリプト');
  console.log('================================');
  console.log(`データベース: ${dbPath}`);

  // データベース接続
  const db = new Database(dbPath);

  try {
    // テーブル存在確認
    const tableExists = db.prepare(`
      SELECT name FROM sqlite_master
      WHERE type='table' AND name='users'
    `).get();

    if (!tableExists) {
      console.log('\nusersテーブルが存在しません。テーブルを作成します...');
      db.exec(`
        CREATE TABLE IF NOT EXISTS users (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          username VARCHAR(50) NOT NULL UNIQUE,
          password_hash VARCHAR(255) NOT NULL,
          display_name VARCHAR(100) NOT NULL,
          email VARCHAR(255),
          role VARCHAR(20) NOT NULL DEFAULT 'viewer',
          venue_id INTEGER,
          is_active BOOLEAN NOT NULL DEFAULT 1,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
      `);
      console.log('usersテーブルを作成しました。');
    }

    // 既存ユーザー確認
    const existing = db.prepare('SELECT id FROM users WHERE username = ?').get(admin.username);

    if (existing) {
      console.log(`\nユーザー '${admin.username}' は既に存在します (ID: ${existing.id})`);
      console.log('パスワードをリセットします...');

      // パスワードハッシュ生成
      const salt = bcrypt.genSaltSync(10);
      const hash = bcrypt.hashSync(admin.password, salt);

      // パスワード更新
      db.prepare('UPDATE users SET password_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE username = ?')
        .run(hash, admin.username);

      console.log('パスワードをリセットしました。');
    } else {
      console.log(`\n管理者 '${admin.username}' を作成します...`);

      // パスワードハッシュ生成
      const salt = bcrypt.genSaltSync(10);
      const hash = bcrypt.hashSync(admin.password, salt);

      // ユーザー挿入
      const result = db.prepare(`
        INSERT INTO users (username, password_hash, display_name, role, is_active)
        VALUES (?, ?, ?, ?, 1)
      `).run(admin.username, hash, admin.display_name, admin.role);

      console.log(`管理者を作成しました (ID: ${result.lastInsertRowid})`);
    }

    console.log('\n================================');
    console.log('ログイン情報:');
    console.log(`  ユーザー名: ${admin.username}`);
    console.log(`  パスワード: ${admin.password}`);
    console.log('================================');

  } catch (error) {
    console.error('エラー:', error.message);
    process.exit(1);
  } finally {
    db.close();
  }
}

main();
