def get_clean_cart(session):
    """
    ดึง cart จาก session แล้วทำความสะอาด:
    - ถ้าไม่ใช่ list → reset เป็น list ว่าง
    - เก็บเฉพาะค่าที่เป็นตัวเลข (int)
    """
    cart = session.get("cart", [])
    if not isinstance(cart, list):
        cart = []

    clean_cart = []
    for i in cart:
        try:
            clean_cart.append(int(i))
        except (ValueError, TypeError):
            continue

    session["cart"] = clean_cart
    return clean_cart
