package com.kingsgrillz.receiptstudio

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.widget.ArrayAdapter
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.Spinner
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.FileProvider
import java.io.File

class MainActivity : AppCompatActivity() {
    private lateinit var store: Store
    private lateinit var name: EditText
    private lateinit var phone: EditText
    private lateinit var product: EditText
    private lateinit var quantity: EditText
    private lateinit var price: EditText
    private lateinit var fee: EditText
    private lateinit var preparation: Spinner
    private lateinit var fulfilment: Spinner
    private lateinit var kind: Spinner
    private lateinit var history: TextView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        store = Store(this)
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(32, 32, 32, 32)
            setBackgroundColor(0xFFFAF7F0.toInt())
        }
        root.addView(title("KING'S GRILLZ"))
        root.addView(label("Offline receipt studio. Android records stay on this device."))
        name = field("Customer name")
        phone = field("Phone")
        product = field("Product").apply { setText("Signature Smoked Guinea Fowl") }
        quantity = field("Quantity").apply { setText("1") }
        price = field("Unit price (₦)").apply { setText("14000") }
        fee = field("Delivery fee (₦)").apply { setText("0") }
        preparation = spinner(listOf("Whole", "Chopped"))
        fulfilment = spinner(listOf("Pickup", "Delivery"))
        kind = spinner(listOf("Invoice (unpaid)", "Receipt (paid)"))
        listOf(name, phone, product, quantity, price, fee).forEach { root.addView(it) }
        root.addView(label("Preparation"))
        root.addView(preparation)
        root.addView(label("Fulfilment"))
        root.addView(fulfilment)
        root.addView(label("Document"))
        root.addView(kind)
        root.addView(button("Save PDF") { save("pdf") })
        root.addView(button("Save PNG") { save("png") })
        root.addView(button("Share to WhatsApp") { save("share") })
        root.addView(button("Backup database") { backup() })
        history = TextView(this).apply { textSize = 14f; setPadding(0, 24, 0, 0) }
        root.addView(history)
        setContentView(ScrollView(this).apply { addView(root) })
        refresh()
    }

    private fun title(text: String) = TextView(this).apply {
        this.text = text
        textSize = 22f
        setTextColor(0xFFD9A441.toInt())
    }

    private fun label(text: String) = TextView(this).apply {
        this.text = text
        setPadding(0, 12, 0, 4)
    }

    private fun field(hint: String) = EditText(this).apply { this.hint = hint }

    private fun spinner(items: List<String>) = Spinner(this).apply {
        adapter = ArrayAdapter(this@MainActivity, android.R.layout.simple_spinner_dropdown_item, items)
    }

    private fun button(text: String, action: () -> Unit) = Button(this).apply {
        this.text = text
        setOnClickListener { action() }
    }

    private fun save(mode: String) {
        val customer = name.text.toString().trim()
        val mobile = phone.text.toString().trim()
        val item = product.text.toString().trim()
        if (customer.isEmpty() || mobile.isEmpty() || item.isEmpty()) {
            toast("Name, phone and product are required")
            return
        }
        val qty = quantity.text.toString().toIntOrNull() ?: 1
        val unit = price.text.toString().toIntOrNull() ?: 0
        val delivery = if (fulfilment.selectedItem == "Delivery") fee.text.toString().toIntOrNull() ?: 0 else 0
        val subtotal = qty * unit
        val total = subtotal + delivery
        val paid = kind.selectedItemPosition == 1
        val draft = Receipt(
            id = 0, number = "", kind = if (paid) "receipt" else "invoice",
            customerName = customer, customerPhone = mobile, productName = item,
            quantity = qty, unitPrice = unit, preparation = preparation.selectedItem.toString(),
            fulfilment = fulfilment.selectedItem.toString(), deliveryFee = delivery,
            subtotal = subtotal, total = total, amountPaid = if (paid) total else 0,
            paymentStatus = if (paid) "paid" else "unpaid", notes = "", createdAt = "",
        )
        val saved = store.save(draft)
        val folder = File(getExternalFilesDir(null), "exports").apply { mkdirs() }
        val pdf = writePdf(this, saved, File(folder, "${saved.number}.pdf"))
        if (mode == "png") writePng(this, saved, File(folder, "${saved.number}.png"))
        refresh()
        if (mode == "share") share(saved, pdf) else toast("Saved ${saved.number}")
    }

    private fun share(doc: Receipt, pdf: File) {
        val uri = FileProvider.getUriForFile(this, "$packageName.fileprovider", pdf)
        val message = "Hello ${doc.customerName},\nYour ${doc.kind} ${doc.number} from KING'S GRILLZ is ready.\nTotal: ${naira(doc.total)}\nStatus: ${doc.paymentStatus.uppercase()}"
        val send = Intent(Intent.ACTION_SEND).apply {
            type = "application/pdf"
            putExtra(Intent.EXTRA_STREAM, uri)
            putExtra(Intent.EXTRA_TEXT, message)
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            setPackage("com.whatsapp")
        }
        if (send.resolveActivity(packageManager) == null) send.setPackage(null)
        startActivity(Intent.createChooser(send, "Share receipt"))
    }

    private fun backup() {
        val source = store.databaseFile(this)
        val folder = File(getExternalFilesDir(null), "exports").apply { mkdirs() }
        val target = File(folder, "receipts-backup.db")
        source.copyTo(target, overwrite = true)
        val uri = FileProvider.getUriForFile(this, "$packageName.fileprovider", target)
        startActivity(Intent.createChooser(Intent(Intent.ACTION_SEND).apply {
            type = "application/octet-stream"
            putExtra(Intent.EXTRA_STREAM, uri)
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }, "Save backup"))
    }

    private fun refresh() {
        history.text = store.list().joinToString("\n") {
            "${it.number}  ${it.customerName}  ${naira(it.total)}  ${it.paymentStatus.uppercase()}"
        }.ifBlank { "No receipts yet." }
    }

    private fun toast(text: String) = Toast.makeText(this, text, Toast.LENGTH_LONG).show()
}
