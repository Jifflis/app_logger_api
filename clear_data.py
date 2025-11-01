from app import create_app, db

def clear_database():
    print("⚠️  This will delete ALL data. Type 'yes' to continue:", end=" ")
    confirm = input().strip().lower()
    if confirm != "yes":
        print("Cancelled.")
        return

    with app.app_context():
        db.drop_all()
        db.create_all()
        print("✅ Database cleared and recreated successfully.")

if __name__ == "__main__":
    app = create_app()
    clear_database()
