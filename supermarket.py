
# supermarket_gui.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
from datetime import datetime

# try to use Pillow for robust image resizing; fallback to PhotoImage
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False

DATA_FILE = "products.json"
DEFAULT_IMAGE = "images/no_image.png"

# ---------- Helper utilities ----------
def load_products():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    # default sample if no file
    return [
        {"name": "Milk", "price": 25000, "stock": 10, "image":DEFAULT_IMAGE},
        {"name": "Bread", "price": 8000, "stock": 20, "image": DEFAULT_IMAGE},
        {"name": "Eggs", "price": 30000, "stock": 6, "image": DEFAULT_IMAGE},
    ]

def save_products():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(products, f, ensure_ascii=False, indent=2)
    except Exception as e:
        messagebox.showerror("Error", f"Couldn't save products: {e}")

def format_currency(x):
    return f"{x:,} تومان"

def load_image(path, size=(80,80)):
    # return a PhotoImage (tk image). Keep references to avoid GC.
    if not os.path.exists(path):
        path = DEFAULT_IMAGE if os.path.exists(DEFAULT_IMAGE) else None

    if PIL_AVAILABLE and path:
        try:
            img = Image.open(path)
            img.thumbnail(size, Image.LANCZOS)
            return ImageTk.PhotoImage(img)
        except Exception:
            pass
    # fallback
    try:
        return tk.PhotoImage(file=path) if path else None
    except Exception:
        return None

# ---------- Data ----------
# ---------- Data ----------
products = [
    {"name": "Milk", "price": 25000, "stock": 10, "image": "images/milk.png"},
    {"name": "Bread", "price": 8000, "stock": 20, "image": "images/bread.png"},
    {"name": "Eggs", "price": 30000, "stock": 6, "image": "images/eggs.png"},
]
cart = []
image_cache = {}

# ---------- UI ----------
root = tk.Tk()
root.title("سوپرمارکت ساده")
root.geometry("900x600")

# Top menu / toolbar
toolbar = ttk.Frame(root, padding=6)
toolbar.pack(fill="x")

btn_admin = ttk.Button(toolbar, text="پنل مسئول فروش (Admin)", command=lambda: open_admin_dialog())
btn_admin.pack(side="left", padx=4)
btn_refresh = ttk.Button(toolbar, text="رفرش محصولات", command=lambda: refresh_products_view())
btn_refresh.pack(side="left", padx=4)
btn_invoice = ttk.Button(toolbar, text="نمایش فاکتور", command=lambda: show_invoice_window())
btn_invoice.pack(side="left", padx=4)

main_frame = ttk.Frame(root)
main_frame.pack(fill="both", expand=True, padx=8, pady=8)

# Left: products list
left_frame = ttk.Frame(main_frame)
left_frame.pack(side="left", fill="both", expand=True)

lbl_products = ttk.Label(left_frame, text="محصولات موجود", font=("Helvetica", 14))
lbl_products.pack(anchor="w", pady=(0,6))

canvas = tk.Canvas(left_frame)
scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=canvas.yview)
products_container = ttk.Frame(canvas)

products_container.bind(
    "<Configure>",
    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
)
canvas.create_window((0,0), window=products_container, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)

canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

# Right: cart
right_frame = ttk.Frame(main_frame, width=260)
right_frame.pack(side="right", fill="y")
lbl_cart = ttk.Label(right_frame, text="سبد خرید", font=("Helvetica", 14))
lbl_cart.pack(anchor="w", pady=(0,6))

cart_listbox = tk.Listbox(right_frame, width=40, height=20)
cart_listbox.pack(padx=4, pady=4)

lbl_total = ttk.Label(right_frame, text="جمع کل: ۰ تومان", font=("Helvetica", 12))
lbl_total.pack(pady=(6,12))

btn_remove = ttk.Button(right_frame, text="حذف آیتم انتخاب‌شده", command=lambda: remove_cart_item())
btn_remove.pack(fill="x", padx=6, pady=2)
btn_clear = ttk.Button(right_frame, text="خالی کردن سبد", command=lambda: clear_cart())
btn_clear.pack(fill="x", padx=6, pady=2)
btn_save_invoice = ttk.Button(right_frame, text="ذخیره فاکتور", command=lambda: save_invoice_to_file())
btn_save_invoice.pack(fill="x", padx=6, pady=6)

# ---------- Product display / operations ----------
def refresh_products_view():
    for w in products_container.winfo_children():
        w.destroy()

    for idx, p in enumerate(products):
        f = ttk.Frame(products_container, relief="ridge", padding=6)
        f.pack(fill="x", pady=4)

        img = image_cache.get(p['image'])
        if img is None:
            img = load_image(p['image'], size=(80,80))
            image_cache[p['image']] = img

        left = ttk.Frame(f)
        left.pack(side="left")
        if img:
            lbl_img = ttk.Label(left, image=img)
            lbl_img.image = img
            lbl_img.pack()
        else:
            ttk.Label(left, text="[تصویر]").pack()

        info_text = f"{idx+1}. {p['name']}\nقیمت: {format_currency(p['price'])}\nموجودی: {p['stock']}"
        ttk.Label(f, text=info_text).pack(side="left", padx=8)

        # buy area
        buy_frame = ttk.Frame(f)
        buy_frame.pack(side="right")
        qty_var = tk.IntVar(value=1)
        ttk.Label(buy_frame, text="تعداد").pack(anchor="e")
        spin = ttk.Spinbox(buy_frame, from_=1, to=max(1, p['stock']), textvariable=qty_var, width=5)
        spin.pack()
        btn_buy = ttk.Button(buy_frame, text="افزودن به سبد", command=lambda i=idx, q=qty_var: buy_product(i, q.get()))
        btn_buy.pack(pady=4)

def buy_product(index, qty):
    try:
        qty = int(qty)
        if qty <= 0:
            raise ValueError
    except Exception:
        messagebox.showerror("ورودی نامعتبر", "تعداد باید عدد مثبت باشد.")
        return

    if index < 0 or index >= len(products):
        messagebox.showerror("خطا", "محصول انتخاب شده معتبر نیست.")
        return

    p = products[index]
    if qty > p['stock']:
        messagebox.showerror("خطا", "تعداد درخواستی بیشتر از موجودی است.")
        return

    p['stock'] -= qty
    # aggregate same item in cart
    for it in cart:
        if it['name'] == p['name'] and it['price'] == p['price']:
            it['qty'] += qty
            break
    else:
        cart.append({"name": p['name'], "price": p['price'], "qty": qty})

    update_cart_view()
    save_products()
    refresh_products_view()

def update_cart_view():
    cart_listbox.delete(0, tk.END)
    total = 0
    for it in cart:
        line = f"{it['name']} — {it['qty']} x {format_currency(it['price'])} = {format_currency(it['qty']*it['price'])}"
        cart_listbox.insert(tk.END, line)
        total += it['qty'] * it['price']
    lbl_total.config(text=f"جمع کل: {format_currency(total)}")

def remove_cart_item():
    sel = cart_listbox.curselection()
    if not sel:
        messagebox.showinfo("انتخاب", "یک آیتم از سبد انتخاب کنید.")
        return
    idx = sel[0]
    # return qty to stock
    it = cart.pop(idx)
    # find product and add back the qty
    for p in products:
        if p['name'] == it['name'] and p['price'] == it['price']:
            p['stock'] += it['qty']
            break
    update_cart_view()
    save_products()
    refresh_products_view()

def clear_cart():
    if not cart:
        return
    # restore stocks
    for it in cart:
        for p in products:
            if p['name'] == it['name'] and p['price'] == it['price']:
                p['stock'] += it['qty']
                break
    cart.clear()
    update_cart_view()
    save_products()
    refresh_products_view()

# ---------- Admin: add/edit products ----------
def open_admin_dialog():
    pwd = simpledialog = None
    # simple password dialog using askstring from tk
    pwd = tk.simpledialog.askstring("Admin Login", "رمز عبور ادمین را وارد کنید:", show='*')
    if pwd != "admin123":
        messagebox.showerror("دسترسی رد شد", "رمز اشتباه است.")
        return

    admin_win = tk.Toplevel(root)
    admin_win.title("پنل ادمین - افزودن محصول")
    admin_win.geometry("420x320")
    ttk.Label(admin_win, text="افزودن / ویرایش محصول", font=("Helvetica", 12)).pack(pady=6)

    frm = ttk.Frame(admin_win, padding=8)
    frm.pack(fill="both", expand=True)

    ttk.Label(frm, text="نام محصول:").grid(row=0, column=0, sticky="e")
    ent_name = ttk.Entry(frm, width=30)
    ent_name.grid(row=0, column=1, pady=4)

    ttk.Label(frm, text="قیمت (تومان):").grid(row=1, column=0, sticky="e")
    ent_price = ttk.Entry(frm, width=30)
    ent_price.grid(row=1, column=1, pady=4)

    ttk.Label(frm, text="موجودی:").grid(row=2, column=0, sticky="e")
    ent_stock = ttk.Entry(frm, width=30)
    ent_stock.grid(row=2, column=1, pady=4)

    ttk.Label(frm, text="تصویر (اختیاری):").grid(row=3, column=0, sticky="e")
    ent_image = ttk.Entry(frm, width=30)
    ent_image.grid(row=3, column=1, pady=4)

    def choose_image():
        p = filedialog.askopenfilename(title="انتخاب تصویر", filetypes=[("PNG/PNG", "*.png *.jpg *.jpeg *.gif"), ("All", "*.*")])
        if p:
            ent_image.delete(0, tk.END)
            ent_image.insert(0, p)

    btn_choose = ttk.Button(frm, text="انتخاب فایل...", command=choose_image)
    btn_choose.grid(row=3, column=2, padx=4)

    def add_new_product():
        name = ent_name.get().strip()
        price = ent_price.get().strip()
        stock = ent_stock.get().strip()
        image = ent_image.get().strip() or DEFAULT_IMAGE

        if not name:
            messagebox.showerror("خطا", "نام محصول را وارد کنید.")
            return
        try:
            price_i = int(price)
            stock_i = int(stock)
            if price_i < 0 or stock_i < 0:
                raise ValueError
        except Exception:
            messagebox.showerror("خطا", "قیمت و موجودی باید اعداد صحیح مثبت باشند.")
            return

        products.append({"name": name, "price": price_i, "stock": stock_i, "image": image})
        save_products()
        refresh_products_view()
        messagebox.showinfo("موفق", "محصول با موفقیت افزوده شد.")
        admin_win.destroy()

    btn_add = ttk.Button(frm, text="افزودن محصول", command=add_new_product)
    btn_add.grid(row=4, column=1, pady=12)

# ---------- Invoice ----------
def show_invoice_window():
    if not cart:
        messagebox.showinfo("سبد خالی", "سبد خرید خالی است.")
        return
    inv_win = tk.Toplevel(root)
    inv_win.title("فاکتور خرید")
    inv_win.geometry("480x400")
    txt = tk.Text(inv_win, wrap="word")
    txt.pack(fill="both", expand=True, padx=8, pady=8)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total = 0
    txt.insert(tk.END, f"فاکتور خرید - {now}\n\n")
    txt.insert(tk.END, "-"*40 + "\n")
    for it in cart:
        line = f"{it['name']} — {it['qty']} x {it['price']:,} = {(it['qty']*it['price']):,}\n"
        txt.insert(tk.END, line)
        total += it['qty'] * it['price']
    txt.insert(tk.END, "-"*40 + "\n")
    txt.insert(tk.END, f"جمع کل: {total:,} تومان\n")
    txt.config(state="disabled")

def save_invoice_to_file():
    if not cart:
        messagebox.showinfo("سبد خالی", "سبد خرید خالی است.")
        return
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = filedialog.asksaveasfilename(defaultextension=".txt", initialfile=f"invoice_{now}.txt",
                                         filetypes=[("Text files","*.txt"), ("All files","*.*")])
    if not fname:
        return
    try:
        with open(fname, "w", encoding="utf-8") as f:
            f.write(f"فاکتور خرید - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("-"*40 + "\n")
            total = 0
            for it in cart:
                f.write(f"{it['name']} — {it['qty']} x {it['price']:,} = {(it['qty']*it['price']):,}\n")
                total += it['qty'] * it['price']
            f.write("-"*40 + "\n")
            f.write(f"جمع کل: {total:,} تومان\n")
        messagebox.showinfo("ذخیره شد", f"فاکتور در {fname} ذخیره شد.")
    except Exception as e:
        messagebox.showerror("خطا", f"ذخیره امکان‌پذیر نبود: {e}")

# initial populate
refresh_products_view()
update_cart_view()

root.mainloop()