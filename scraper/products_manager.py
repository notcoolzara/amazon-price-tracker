# scraper/products_manager.py

import json
import os
import csv
from datetime import datetime
from typing import List, Dict, Optional
from config import PRODUCTS_DB_PATH


class ProductsManager:
    """Manage tracked products in JSON database"""
    
    def __init__(self):
        self.db_path = PRODUCTS_DB_PATH
        self._ensure_db()
    
    def _ensure_db(self):
        """Create database file if it doesn't exist"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        if not os.path.exists(self.db_path):
            self._write_db({"products": []})
    
    def _read_db(self) -> Dict:
        """Read database file"""
        try:
            with open(self.db_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[!] Error reading database: {e}")
            return {"products": []}
    
    def _write_db(self, data: Dict):
        """Write to database file"""
        try:
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[!] Error writing database: {e}")
    
    def load_products(self) -> List[Dict]:
        """Load all products from database"""
        data = self._read_db()
        return data.get("products", [])
    
    def save_products(self, products: List[Dict]):
        """Save products to database"""
        self._write_db({"products": products})
    
    def add_product(self, asin: str, name: str, target_price: Optional[float] = None, 
                    stock_alert: bool = False, alert_channels: Optional[List[str]] = None) -> bool:
        """Add a new product to track"""
        products = self.load_products()
        
        # Check if ASIN already exists
        if any(p["asin"] == asin for p in products):
            print(f"[!] Product {asin} already exists")
            return False
        
        # Create new product entry
        product = {
            "asin": asin,
            "name": name,
            "target_price": target_price,
            "stock_alert": stock_alert,
            "alert_channels": alert_channels if alert_channels else ["email"],
            "enabled": True,
            "created_at": datetime.now().isoformat(),
            "last_checked": None
        }
        
        products.append(product)
        self.save_products(products)
        print(f"[OK] Added product: {name} ({asin})")
        return True
    
    def update_product(self, asin: str, **kwargs) -> bool:
        """Update product details"""
        products = self.load_products()
        
        for product in products:
            if product["asin"] == asin:
                # Update only provided fields
                for key, value in kwargs.items():
                    product[key] = value
                
                self.save_products(products)
                print(f"[OK] Updated product: {asin}")
                return True
        
        print(f"[!] Product {asin} not found")
        return False
    
    def delete_product(self, asin: str) -> bool:
        """Delete a product by ASIN"""
        products = self.load_products()
        original_count = len(products)
        
        # Filter out the product to delete
        products = [p for p in products if p["asin"] != asin]
        
        if len(products) < original_count:
            self.save_products(products)
            print(f"[OK] Deleted product: {asin}")
            return True
        
        print(f"[!] Product {asin} not found")
        return False
    
    def get_product(self, asin: str) -> Optional[Dict]:
        """Get a single product by ASIN"""
        products = self.load_products()
        for product in products:
            if product["asin"] == asin:
                return product
        return None
    
    def get_enabled_products(self) -> List[Dict]:
        """Get all enabled products"""
        products = self.load_products()
        return [p for p in products if p.get("enabled", True)]
    
    def toggle_product(self, asin: str) -> bool:
        """Enable/disable a product"""
        products = self.load_products()
        
        for product in products:
            if product["asin"] == asin:
                current_status = product.get("enabled", True)
                product["enabled"] = not current_status
                self.save_products(products)
                
                status = "enabled" if product["enabled"] else "disabled"
                print(f"[OK] Product {asin} {status}")
                return True
        
        print(f"[!] Product {asin} not found")
        return False
    
    def import_from_csv(self, csv_path: str) -> int:
        """Import products from CSV file
        
        Expected CSV format:
        asin,name,target_price
        B08N5WRWNW,Echo Dot,29.99
        """
        if not os.path.exists(csv_path):
            print(f"[!] CSV file not found: {csv_path}")
            return 0
        
        count = 0
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    asin = row.get('asin', '').strip()
                    name = row.get('name', '').strip()
                    target_price_str = row.get('target_price', '').strip()
                    
                    if not asin or not name:
                        continue
                    
                    # Parse target price
                    target_price = None
                    if target_price_str:
                        try:
                            target_price = float(target_price_str)
                        except ValueError:
                            print(f"[!] Invalid price for {asin}: {target_price_str}")
                    
                    # Add product
                    if self.add_product(asin, name, target_price):
                        count += 1
            
            print(f"[OK] Imported {count} products from CSV")
            return count
            
        except Exception as e:
            print(f"[!] Error importing CSV: {e}")
            return 0
    
    def export_to_csv(self, csv_path: str) -> bool:
        """Export products to CSV file"""
        products = self.load_products()
        
        if not products:
            print("[!] No products to export")
            return False
        
        try:
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                fieldnames = ['asin', 'name', 'target_price', 'stock_alert', 'enabled']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                writer.writeheader()
                
                for product in products:
                    writer.writerow({
                        'asin': product['asin'],
                        'name': product['name'],
                        'target_price': product.get('target_price', ''),
                        'stock_alert': product.get('stock_alert', False),
                        'enabled': product.get('enabled', True)
                    })
            
            print(f"[OK] Exported {len(products)} products to {csv_path}")
            return True
            
        except Exception as e:
            print(f"[!] Error exporting CSV: {e}")
            return False
    
    def clear_all(self) -> bool:
        """Delete all products (use with caution)"""
        try:
            self.save_products([])
            print("[OK] All products cleared")
            return True
        except Exception as e:
            print(f"[!] Error clearing products: {e}")
            return False
    
    def get_stats(self) -> Dict:
        """Get statistics about tracked products"""
        products = self.load_products()
        
        enabled = [p for p in products if p.get("enabled", True)]
        with_target_price = [p for p in products if p.get("target_price") is not None]
        with_stock_alert = [p for p in products if p.get("stock_alert", False)]
        
        return {
            "total": len(products),
            "enabled": len(enabled),
            "disabled": len(products) - len(enabled),
            "with_target_price": len(with_target_price),
            "with_stock_alert": len(with_stock_alert)
        }


# CLI usage example
if __name__ == "__main__":
    manager = ProductsManager()
    
    # Example: Add a product
    manager.add_product(
        asin="B08N5WRWNW",
        name="Echo Dot (4th Gen)",
        target_price=29.99,
        stock_alert=False,
        alert_channels=["email", "telegram"]
    )
    
    # Example: List all products
    products = manager.load_products()
    print(f"\nTotal products: {len(products)}")
    for p in products:
        print(f"  - {p['name']} ({p['asin']})")
    
    # Example: Get stats
    stats = manager.get_stats()
    print(f"\nStats: {stats}")