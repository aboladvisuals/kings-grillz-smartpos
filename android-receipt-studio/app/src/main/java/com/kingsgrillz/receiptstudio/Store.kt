package com.kingsgrillz.receiptstudio

import android.content.ContentValues
import android.content.Context
import android.database.sqlite.SQLiteDatabase
import android.database.sqlite.SQLiteOpenHelper
import java.io.File
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

data class Receipt(
    val id: Long,
    val number: String,
    val kind: String,
    val customerName: String,
    val customerPhone: String,
    val productName: String,
    val quantity: Int,
    val unitPrice: Int,
    val preparation: String,
    val fulfilment: String,
    val deliveryFee: Int,
    val subtotal: Int,
    val total: Int,
    val amountPaid: Int,
    val paymentStatus: String,
    val notes: String,
    val createdAt: String,
)

data class BusinessSettings(
    val bankName: String = "PalmPay",
    val accountName: String = "Kings Grillz Ventures",
    val accountNumber: String = "9552604707",
)

class Store(context: Context) : SQLiteOpenHelper(context, "receipts.db", null, 1) {
    override fun onCreate(db: SQLiteDatabase) {
        db.execSQL(
            """
            CREATE TABLE documents (
                id INTEGER PRIMARY KEY,
                number TEXT NOT NULL UNIQUE,
                kind TEXT NOT NULL,
                customer_name TEXT NOT NULL,
                customer_phone TEXT NOT NULL,
                product_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price INTEGER NOT NULL,
                preparation TEXT NOT NULL,
                fulfilment TEXT NOT NULL,
                delivery_fee INTEGER NOT NULL,
                subtotal INTEGER NOT NULL,
                total INTEGER NOT NULL,
                amount_paid INTEGER NOT NULL,
                payment_status TEXT NOT NULL,
                notes TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """.trimIndent()
        )
        db.execSQL("CREATE TABLE counters (day TEXT PRIMARY KEY, value INTEGER NOT NULL)")
        db.execSQL("CREATE TABLE settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    }

    override fun onUpgrade(db: SQLiteDatabase, oldVersion: Int, newVersion: Int) = Unit

    fun nextNumber(): String {
        val day = SimpleDateFormat("yyyyMMdd", Locale.US).format(Date())
        val db = writableDatabase
        val cursor = db.rawQuery("SELECT value FROM counters WHERE day = ?", arrayOf(day))
        val current = if (cursor.moveToFirst()) cursor.getInt(0) else 0
        cursor.close()
        val next = current + 1
        val values = ContentValues().apply {
            put("day", day)
            put("value", next)
        }
        db.insertWithOnConflict("counters", null, values, SQLiteDatabase.CONFLICT_REPLACE)
        return "KGA-$day-${next.toString().padStart(4, '0')}"
    }

    fun save(doc: Receipt): Receipt {
        val number = nextNumber()
        val created = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss", Locale.US).format(Date())
        val values = ContentValues().apply {
            put("number", number)
            put("kind", doc.kind)
            put("customer_name", doc.customerName)
            put("customer_phone", doc.customerPhone)
            put("product_name", doc.productName)
            put("quantity", doc.quantity)
            put("unit_price", doc.unitPrice)
            put("preparation", doc.preparation)
            put("fulfilment", doc.fulfilment)
            put("delivery_fee", doc.deliveryFee)
            put("subtotal", doc.subtotal)
            put("total", doc.total)
            put("amount_paid", doc.amountPaid)
            put("payment_status", doc.paymentStatus)
            put("notes", doc.notes)
            put("created_at", created)
        }
        val id = writableDatabase.insert("documents", null, values)
        return doc.copy(id = id, number = number, createdAt = created)
    }

    fun list(query: String = ""): List<Receipt> {
        val sql = if (query.isBlank()) {
            "SELECT * FROM documents ORDER BY id DESC"
        } else {
            "SELECT * FROM documents WHERE number LIKE ? OR customer_name LIKE ? OR customer_phone LIKE ? ORDER BY id DESC"
        }
        val args = if (query.isBlank()) emptyArray() else Array(3) { "%$query%" }
        val cursor = readableDatabase.rawQuery(sql, args)
        val items = mutableListOf<Receipt>()
        while (cursor.moveToNext()) {
            items.add(
                Receipt(
                    id = cursor.getLong(0),
                    number = cursor.getString(1),
                    kind = cursor.getString(2),
                    customerName = cursor.getString(3),
                    customerPhone = cursor.getString(4),
                    productName = cursor.getString(5),
                    quantity = cursor.getInt(6),
                    unitPrice = cursor.getInt(7),
                    preparation = cursor.getString(8),
                    fulfilment = cursor.getString(9),
                    deliveryFee = cursor.getInt(10),
                    subtotal = cursor.getInt(11),
                    total = cursor.getInt(12),
                    amountPaid = cursor.getInt(13),
                    paymentStatus = cursor.getString(14),
                    notes = cursor.getString(15),
                    createdAt = cursor.getString(16),
                )
            )
        }
        cursor.close()
        return items
    }

    fun loadSettings(): BusinessSettings {
        val cursor = readableDatabase.rawQuery("SELECT value FROM settings WHERE key = ?", arrayOf("bank"))
        val raw = if (cursor.moveToFirst()) cursor.getString(0) else null
        cursor.close()
        if (raw.isNullOrBlank()) return BusinessSettings()
        val parts = raw.split("|")
        return BusinessSettings(
            bankName = parts.getOrNull(0)?.ifBlank { "PalmPay" } ?: "PalmPay",
            accountName = parts.getOrNull(1)?.ifBlank { "Kings Grillz Ventures" } ?: "Kings Grillz Ventures",
            accountNumber = parts.getOrNull(2)?.ifBlank { "9552604707" } ?: "9552604707",
        )
    }

    fun saveSettings(settings: BusinessSettings) {
        val value = "${settings.bankName}|${settings.accountName}|${settings.accountNumber}"
        val values = ContentValues().apply {
            put("key", "bank")
            put("value", value)
        }
        writableDatabase.insertWithOnConflict("settings", null, values, SQLiteDatabase.CONFLICT_REPLACE)
    }

    fun databaseFile(context: Context): File = context.getDatabasePath("receipts.db")
}
