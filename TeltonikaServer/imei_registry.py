#!/usr/bin/env python3
"""
IMEI Registry - sleduje a ukládá informace o všech Teltonika zařízeních
"""

import json
import os
from datetime import datetime
from typing import Dict, Optional, List

class IMEIRegistry:
    def __init__(self, registry_path: str):
        self.registry_path = registry_path
        self.registry = self._load_registry()
    
    def _load_registry(self) -> Dict:
        """Načte IMEI registr ze souboru"""
        try:
            if os.path.exists(self.registry_path):
                with open(self.registry_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Chyba při načítání IMEI registru: {e}")
        return {}
    
    def _save_registry(self):
        """Uloží IMEI registr do souboru"""
        try:
            # Zajisti, že složka existuje
            os.makedirs(os.path.dirname(self.registry_path), exist_ok=True)
            
            with open(self.registry_path, 'w', encoding='utf-8') as f:
                json.dump(self.registry, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Chyba při ukládání IMEI registru: {e}")
    
    def register_imei_connection(self, imei: str, ip_address: str) -> bool:
        """
        Zaregistruje nové připojení IMEI zařízení
        Returns: True pokud je IMEI nové, False pokud už existuje
        """
        now = datetime.now().isoformat()
        is_new_imei = imei not in self.registry
        
        if is_new_imei:
            # Nové IMEI
            self.registry[imei] = {
                "first_seen": now,
                "last_seen": now,
                "total_connections": 1,
                "total_records": 0,
                "ip_addresses": [ip_address],
                "last_ip": ip_address,
                "device_info": {
                    "model": "unknown",
                    "firmware": "unknown"
                }
            }
            print(f"📱 Nové IMEI zařízení registrováno: {imei}")
        else:
            # Existující IMEI - aktualizuj
            entry = self.registry[imei]
            entry["last_seen"] = now
            entry["total_connections"] += 1
            entry["last_ip"] = ip_address
            
            # Přidej IP do seznamu pokud není
            if ip_address not in entry["ip_addresses"]:
                entry["ip_addresses"].append(ip_address)
                # Omez seznam na posledních 10 IP adres
                entry["ip_addresses"] = entry["ip_addresses"][-10:]
        
        self._save_registry()
        return is_new_imei
    
    def register_avl_records(self, imei: str, record_count: int):
        """Zaregistruje počet přijatých AVL záznamů"""
        if imei in self.registry:
            self.registry[imei]["total_records"] += record_count
            self.registry[imei]["last_seen"] = datetime.now().isoformat()
            self._save_registry()
    
    def get_imei_info(self, imei: str) -> Optional[Dict]:
        """Vrátí informace o IMEI zařízení"""
        return self.registry.get(imei)
    
    def get_all_imeis(self) -> List[str]:
        """Vrátí seznam všech známých IMEI"""
        return list(self.registry.keys())
    
    def get_registry_stats(self) -> Dict:
        """Vrátí statistiky registru"""
        if not self.registry:
            return {
                "total_devices": 0,
                "total_connections": 0,
                "total_records": 0
            }
        
        total_connections = sum(entry["total_connections"] for entry in self.registry.values())
        total_records = sum(entry["total_records"] for entry in self.registry.values())
        
        return {
            "total_devices": len(self.registry),
            "total_connections": total_connections,
            "total_records": total_records,
            "devices": list(self.registry.keys())
        }
    
    def is_imei_allowed(self, imei: str, allowed_list: List[str]) -> bool:
        """
        Zkontroluje, zda je IMEI povoleno
        Pokud je seznam prázdný, všechny IMEI jsou povoleny
        """
        if not allowed_list:
            return True
        return imei in allowed_list
    
    def format_registry_summary(self) -> str:
        """Vrátí textový přehled registru"""
        if not self.registry:
            return "Žádná IMEI zařízení zatím nebyla registrována."
        
        summary = f"IMEI Registry - Celkem {len(self.registry)} zařízení:\n\n"
        
        for imei, info in self.registry.items():
            first_seen = datetime.fromisoformat(info["first_seen"]).strftime("%Y-%m-%d %H:%M:%S")
            last_seen = datetime.fromisoformat(info["last_seen"]).strftime("%Y-%m-%d %H:%M:%S") 
            
            summary += f"IMEI: {imei}\n"
            summary += f"  • První připojení: {first_seen}\n"
            summary += f"  • Poslední aktivita: {last_seen}\n" 
            summary += f"  • Celkem připojení: {info['total_connections']}\n"
            summary += f"  • Celkem záznamů: {info['total_records']}\n"
            summary += f"  • Poslední IP: {info['last_ip']}\n"
            summary += f"  • Všechny IP: {', '.join(info['ip_addresses'])}\n\n"
        
        return summary