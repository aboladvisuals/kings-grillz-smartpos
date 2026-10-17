package com.kingsgrillz.receiptstudio

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Typeface
import android.graphics.pdf.PdfDocument
import java.io.File
import java.io.FileOutputStream

fun naira(amount: Int): String = "₦%,d".format(amount)

fun writePdf(context: Context, doc: Receipt, destination: File): File {
    destination.parentFile?.mkdirs()
    val pdf = PdfDocument()
    val page = pdf.startPage(PdfDocument.PageInfo.Builder(595, 842, 1).create())
    val canvas = page.canvas
    val gold = Paint().apply { color = Color.rgb(217, 164, 65); textSize = 22f; typeface = Typeface.DEFAULT_BOLD; textAlign = Paint.Align.CENTER }
    val black = Paint().apply { color = Color.rgb(23, 23, 23); textSize = 12f }
    val grey = Paint().apply { color = Color.rgb(102, 102, 102); textSize = 11f }
    canvas.drawColor(Color.rgb(250, 247, 240))
    var y = 40f
    runCatching {
        context.assets.open("logo.png").use { BitmapFactory.decodeStream(it) }
    }.getOrNull()?.let { logo ->
        val scaled = Bitmap.createScaledBitmap(logo, 90, 90, true)
        canvas.drawBitmap(scaled, (595 - 90) / 2f, y, null)
        y += 100
    }
    canvas.drawText("KING'S GRILLZ", 297f, y, gold)
    y += 22
    canvas.drawText("YOUR PREMIUM AWO PLUG", 297f, y, grey.apply { textAlign = Paint.Align.CENTER })
    y += 28
    val title = if (doc.paymentStatus == "paid") "RECEIPT · PAID" else "INVOICE · UNPAID"
    canvas.drawText(title, 297f, y, black.apply { textSize = 16f; typeface = Typeface.DEFAULT_BOLD; textAlign = Paint.Align.CENTER })
    y += 36
    black.textAlign = Paint.Align.LEFT
    black.textSize = 12f
    black.typeface = Typeface.DEFAULT
    val rows = listOf(
        "Document" to doc.number,
        "Date" to doc.createdAt.replace("T", " "),
        "Customer" to doc.customerName,
        "Phone" to doc.customerPhone,
        "Product" to doc.productName,
        "Preparation" to doc.preparation,
        "Fulfilment" to doc.fulfilment,
        "Quantity" to doc.quantity.toString(),
        "Unit price" to naira(doc.unitPrice),
        "Delivery fee" to naira(doc.deliveryFee),
        "Total" to naira(doc.total),
        "Amount paid" to naira(doc.amountPaid),
        "Balance due" to naira((doc.total - doc.amountPaid).coerceAtLeast(0)),
    )
    rows.forEach { (label, value) ->
        canvas.drawText(label, 40f, y, grey.apply { textAlign = Paint.Align.LEFT })
        canvas.drawText(value, 220f, y, black)
        y += 22
    }
    y += 20
    canvas.drawText("Thank you for choosing KING'S GRILLZ!", 297f, y, gold.apply { textSize = 12f })
    pdf.finishPage(page)
    FileOutputStream(destination).use { pdf.writeTo(it) }
    pdf.close()
    return destination
}

fun writePng(context: Context, doc: Receipt, destination: File): File {
    destination.parentFile?.mkdirs()
    val bitmap = Bitmap.createBitmap(900, 1200, Bitmap.Config.ARGB_8888)
    val canvas = Canvas(bitmap)
    canvas.drawColor(Color.rgb(250, 247, 240))
    val gold = Paint().apply { color = Color.rgb(217, 164, 65); textSize = 42f; typeface = Typeface.DEFAULT_BOLD; textAlign = Paint.Align.CENTER }
    val black = Paint().apply { color = Color.rgb(23, 23, 23); textSize = 28f }
    var y = 50f
    runCatching {
        context.assets.open("logo.png").use { BitmapFactory.decodeStream(it) }
    }.getOrNull()?.let {
        canvas.drawBitmap(Bitmap.createScaledBitmap(it, 140, 140, true), 380f, y, null)
        y += 160
    }
    canvas.drawText("KING'S GRILLZ", 450f, y, gold)
    y += 50
    canvas.drawText(if (doc.paymentStatus == "paid") "RECEIPT · PAID" else "INVOICE · UNPAID", 450f, y, black.apply { textAlign = Paint.Align.CENTER })
    y += 50
    black.textAlign = Paint.Align.LEFT
    listOf(
        doc.number, doc.customerName, doc.customerPhone, doc.productName,
        "${doc.quantity} × ${naira(doc.unitPrice)}", "Total ${naira(doc.total)}",
    ).forEach {
        canvas.drawText(it, 60f, y, black)
        y += 40
    }
    FileOutputStream(destination).use { bitmap.compress(Bitmap.CompressFormat.PNG, 100, it) }
    return destination
}
