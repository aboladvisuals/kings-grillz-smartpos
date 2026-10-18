package com.kingsgrillz.receiptstudio

import android.content.ContentValues
import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Typeface
import android.graphics.pdf.PdfDocument
import android.os.Build
import android.os.Environment
import android.provider.MediaStore
import java.io.File
import java.io.FileOutputStream

fun naira(amount: Int): String = "₦%,d".format(amount)

private fun loadLogo(context: Context): Bitmap? = runCatching {
    context.assets.open("logo.png").use { BitmapFactory.decodeStream(it) }
}.getOrNull()

fun writePdf(context: Context, doc: Receipt, destination: File): File {
    destination.parentFile?.mkdirs()
    val settings = Store(context).loadSettings()
    val pdf = PdfDocument()
    val pageInfo = PdfDocument.PageInfo.Builder(595, 842, 1).create()
    val page = pdf.startPage(pageInfo)
    val canvas = page.canvas
    val isPaid = doc.paymentStatus == "paid"

    // Header bar
    val goldPaint = Paint().apply { color = Color.rgb(217, 164, 65) }
    canvas.drawRect(0f, 0f, 595f, 8f, goldPaint)

    var y = 24f
    loadLogo(context)?.let {
        canvas.drawBitmap(Bitmap.createScaledBitmap(it, 72, 72, true), 262f, y, null)
        y += 84
    }

    val titlePaint = Paint().apply {
        color = Color.rgb(217, 164, 65)
        textSize = 22f
        typeface = Typeface.DEFAULT_BOLD
        textAlign = Paint.Align.CENTER
    }
    canvas.drawText("KING'S GRILLZ", 297f, y, titlePaint)
    y += 20
    val subPaint = Paint().apply {
        color = Color.rgb(23, 23, 23)
        textSize = 11f
        textAlign = Paint.Align.CENTER
    }
    canvas.drawText("YOUR PREMIUM AWO PLUG", 297f, y, subPaint)
    y += 28

    val heading = if (isPaid) "RECEIPT" else "INVOICE"
    val status = if (isPaid) "PAID" else "UNPAID"
    val headPaint = Paint().apply {
        color = Color.rgb(23, 23, 23)
        textSize = 20f
        typeface = Typeface.DEFAULT_BOLD
        textAlign = Paint.Align.CENTER
    }
    canvas.drawText(heading, 297f, y, headPaint)
    y += 18
    val statusPaint = Paint().apply {
        color = if (isPaid) Color.rgb(27, 122, 58) else Color.rgb(230, 107, 36)
        textSize = 14f
        typeface = Typeface.DEFAULT_BOLD
        textAlign = Paint.Align.CENTER
    }
    canvas.drawText(status, 297f, y, statusPaint)
    y += 28

    val labelPaint = Paint().apply { color = Color.rgb(102, 102, 102); textSize = 12f }
    val valuePaint = Paint().apply { color = Color.rgb(23, 23, 23); textSize = 12f; typeface = Typeface.DEFAULT_BOLD }

    fun row(label: String, value: String) {
        canvas.drawText(label, 40f, y, labelPaint)
        canvas.drawText(value, 220f, y, valuePaint)
        y += 20
    }

    row("Invoice number", doc.number)
    row("Date", doc.createdAt.replace("T", " "))
    row("Customer", doc.customerName)
    row("Phone", doc.customerPhone)
    row("Product", doc.productName)
    row("Preparation", doc.preparation)
    row("Fulfilment", doc.fulfilment)
    row("Quantity", doc.quantity.toString())
    row("Unit price", naira(doc.unitPrice))
    row("Subtotal", naira(doc.subtotal))
    row("Delivery fee", naira(doc.deliveryFee))
    row("Total", naira(doc.total))
    row("Amount paid", naira(doc.amountPaid))
    row("Balance due", naira((doc.total - doc.amountPaid).coerceAtLeast(0)))

    if (!isPaid) {
        y += 16
        canvas.drawText("PAYMENT DETAILS", 40f, y, titlePaint.apply { textAlign = Paint.Align.LEFT; textSize = 14f })
        y += 22
        row("Bank", settings.bankName)
        row("Account name", settings.accountName)
        row("Account number", settings.accountNumber)
        y += 8
        val notePaint = Paint().apply { color = Color.rgb(23, 23, 23); textSize = 11f }
        canvas.drawText("Please use your invoice number as the payment reference.", 40f, y, notePaint)
        y += 16
        canvas.drawText("An unpaid invoice is not proof of payment.", 40f, y, notePaint.apply { color = Color.rgb(230, 107, 36) })
    }

    y += 28
    canvas.drawText("Thank you for choosing KING'S GRILLZ!", 297f, y, titlePaint.apply { textAlign = Paint.Align.CENTER; textSize = 12f })

    pdf.finishPage(page)
    FileOutputStream(destination).use { pdf.writeTo(it) }
    pdf.close()
    return destination
}

fun writePng(context: Context, doc: Receipt, destination: File): File {
    destination.parentFile?.mkdirs()
    val settings = Store(context).loadSettings()
    val isPaid = doc.paymentStatus == "paid"
    val height = if (isPaid) 1100 else 1400
    val bitmap = Bitmap.createBitmap(900, height, Bitmap.Config.ARGB_8888)
    val canvas = Canvas(bitmap)
    canvas.drawColor(Color.rgb(250, 247, 240))
    canvas.drawRect(0f, 0f, 900f, 16f, Paint().apply { color = Color.rgb(217, 164, 65) })

    var y = 40f
    loadLogo(context)?.let {
        canvas.drawBitmap(Bitmap.createScaledBitmap(it, 140, 140, true), 380f, y, null)
        y += 160
    }

    val gold = Paint().apply {
        color = Color.rgb(217, 164, 65)
        textSize = 42f
        typeface = Typeface.DEFAULT_BOLD
        textAlign = Paint.Align.CENTER
    }
    canvas.drawText("KING'S GRILLZ", 450f, y, gold)
    y += 40
    val black = Paint().apply { color = Color.rgb(23, 23, 23); textSize = 18f; textAlign = Paint.Align.CENTER }
    canvas.drawText("YOUR PREMIUM AWO PLUG", 450f, y, black)
    y += 50

    val heading = if (isPaid) "RECEIPT" else "INVOICE"
    val status = if (isPaid) "PAID" else "UNPAID"
    canvas.drawText(heading, 450f, y, black.apply { textSize = 32f; typeface = Typeface.DEFAULT_BOLD })
    y += 40
    val statusPaint = Paint().apply {
        textSize = 22f
        typeface = Typeface.DEFAULT_BOLD
        textAlign = Paint.Align.CENTER
        color = if (isPaid) Color.rgb(27, 122, 58) else Color.rgb(230, 107, 36)
    }
    canvas.drawText(status, 450f, y, statusPaint)
    y += 50

    val label = Paint().apply { color = Color.rgb(102, 102, 102); textSize = 20f; textAlign = Paint.Align.LEFT }
    val value = Paint().apply { color = Color.rgb(23, 23, 23); textSize = 20f; typeface = Typeface.DEFAULT_BOLD; textAlign = Paint.Align.RIGHT }

    fun row(l: String, v: String) {
        canvas.drawText(l, 60f, y, label)
        canvas.drawText(v, 840f, y, value)
        y += 36
    }

    row("Invoice number", doc.number)
    row("Date", doc.createdAt.replace("T", " "))
    row("Customer", doc.customerName)
    row("Phone", doc.customerPhone)
    row("Product", doc.productName)
    row("Preparation", doc.preparation)
    row("Fulfilment", doc.fulfilment)
    row("Quantity", doc.quantity.toString())
    row("Unit price", naira(doc.unitPrice))
    row("Subtotal", naira(doc.subtotal))
    row("Delivery fee", naira(doc.deliveryFee))
    row("Total", naira(doc.total))
    row("Amount paid", naira(doc.amountPaid))
    row("Balance due", naira((doc.total - doc.amountPaid).coerceAtLeast(0)))

    if (!isPaid) {
        y += 20
        canvas.drawRect(50f, y - 10, 850f, y + 160, Paint().apply { color = Color.rgb(217, 164, 65); style = Paint.Style.STROKE; strokeWidth = 3f })
        canvas.drawText("PAYMENT DETAILS", 450f, y + 20, gold.apply { textSize = 22f })
        y += 50
        row("Bank", settings.bankName)
        row("Account name", settings.accountName)
        row("Account number", settings.accountNumber)
        y += 10
        val note = Paint().apply { color = Color.rgb(23, 23, 23); textSize = 16f; textAlign = Paint.Align.LEFT }
        canvas.drawText("Use your invoice number as the payment reference.", 60f, y, note)
        y += 24
        canvas.drawText("An unpaid invoice is not proof of payment.", 60f, y, note.apply { color = Color.rgb(230, 107, 36) })
    }

    y += 40
    canvas.drawText("Thank you for choosing KING'S GRILLZ!", 450f, y, gold.apply { textSize = 18f })
    canvas.drawRect(0f, height - 16f, 900f, height.toFloat(), Paint().apply { color = Color.rgb(217, 164, 65) })

    FileOutputStream(destination).use { bitmap.compress(Bitmap.CompressFormat.PNG, 100, it) }
    return destination
}

/** Save a PNG into the device Gallery/Pictures using MediaStore. */
fun saveToGallery(context: Context, pngFile: File, displayName: String): Boolean {
    return try {
        val values = ContentValues().apply {
            put(MediaStore.Images.Media.DISPLAY_NAME, displayName)
            put(MediaStore.Images.Media.MIME_TYPE, "image/png")
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                put(MediaStore.Images.Media.RELATIVE_PATH, Environment.DIRECTORY_PICTURES + "/KingsGrillz")
                put(MediaStore.Images.Media.IS_PENDING, 1)
            }
        }
        val resolver = context.contentResolver
        val uri = resolver.insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, values) ?: return false
        resolver.openOutputStream(uri)?.use { out ->
            pngFile.inputStream().use { it.copyTo(out) }
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            values.clear()
            values.put(MediaStore.Images.Media.IS_PENDING, 0)
            resolver.update(uri, values, null, null)
        }
        true
    } catch (e: Exception) {
        false
    }
}
