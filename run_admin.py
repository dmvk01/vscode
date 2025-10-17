from guide_ai_bot.app.admin.admin_panel import admin_panel

if __name__ == "__main__":
    # Запускаем админ-панель
    admin_panel.run(host="0.0.0.0", port=5000, debug=False)