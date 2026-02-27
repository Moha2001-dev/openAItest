#!/usr/bin/env python3
"""CLI لتتبع القطع الاستهلاكية وصيانات السيارة بناءً على عداد الكيلومترات."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

DATE_FMT = "%Y-%m-%d"
DEFAULT_DB_PATH = Path("car_maintenance_data.json")


@dataclass
class ConsumablePart:
    name: str
    interval_km: int
    last_change_km: int
    notes: str = ""


@dataclass
class ServiceRecord:
    date: str
    mileage_km: int
    title: str
    details: str = ""
    cost: float = 0.0


class TrackerStore:
    def __init__(self, db_path: Path = DEFAULT_DB_PATH):
        self.db_path = db_path
        self.data = self._load()

    def _load(self) -> Dict:
        if not self.db_path.exists():
            return {"current_mileage_km": 0, "parts": [], "service_history": []}
        with self.db_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def save(self) -> None:
        with self.db_path.open("w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    @property
    def current_mileage(self) -> int:
        return int(self.data.get("current_mileage_km", 0))

    def set_current_mileage(self, mileage_km: int) -> None:
        self.data["current_mileage_km"] = mileage_km
        self.save()

    def add_part(self, part: ConsumablePart) -> None:
        parts = self.data["parts"]
        existing = self.find_part(part.name)
        if existing is not None:
            existing.update(asdict(part))
        else:
            parts.append(asdict(part))
        self.save()

    def find_part(self, name: str) -> Optional[Dict]:
        lowered = name.strip().lower()
        for part in self.data["parts"]:
            if part["name"].strip().lower() == lowered:
                return part
        return None

    def change_part(self, name: str, mileage_km: int, notes: str = "") -> bool:
        part = self.find_part(name)
        if part is None:
            return False
        part["last_change_km"] = mileage_km
        if notes:
            part["notes"] = notes
        self.save()
        return True

    def add_service_record(self, record: ServiceRecord) -> None:
        self.data["service_history"].append(asdict(record))
        self.data["service_history"].sort(
            key=lambda x: (x["mileage_km"], x["date"]), reverse=True
        )
        self.save()

    def due_parts(self, at_mileage: Optional[int] = None) -> List[Dict]:
        current = self.current_mileage if at_mileage is None else at_mileage
        results: List[Dict] = []
        for part in self.data["parts"]:
            due_at = part["last_change_km"] + part["interval_km"]
            remaining = due_at - current
            item = {**part, "due_at_km": due_at, "remaining_km": remaining}
            results.append(item)
        results.sort(key=lambda x: x["remaining_km"])
        return results


def positive_int(value: str) -> int:
    number = int(value)
    if number < 0:
        raise argparse.ArgumentTypeError("القيمة يجب أن تكون 0 أو أكبر")
    return number


def date_or_today(value: Optional[str]) -> str:
    if not value:
        return datetime.now().strftime(DATE_FMT)
    datetime.strptime(value, DATE_FMT)
    return value


def cmd_set_mileage(args: argparse.Namespace, store: TrackerStore) -> None:
    store.set_current_mileage(args.km)
    print(f"✅ تم تحديث عداد السيارة إلى {args.km} كم")


def cmd_add_part(args: argparse.Namespace, store: TrackerStore) -> None:
    part = ConsumablePart(
        name=args.name,
        interval_km=args.interval,
        last_change_km=args.last_change,
        notes=args.notes or "",
    )
    store.add_part(part)
    print(f"✅ تمت إضافة/تحديث القطعة: {args.name}")


def cmd_change_part(args: argparse.Namespace, store: TrackerStore) -> None:
    ok = store.change_part(args.name, args.km, args.notes or "")
    if not ok:
        print(f"❌ القطعة '{args.name}' غير موجودة. أضفها أولاً بالأمر add-part")
        return
    print(f"✅ تم تسجيل تغيير القطعة '{args.name}' عند {args.km} كم")


def cmd_due(args: argparse.Namespace, store: TrackerStore) -> None:
    data = store.due_parts(args.at_km)
    if not data:
        print("لا توجد قطع مسجلة حتى الآن.")
        return

    current = args.at_km if args.at_km is not None else store.current_mileage
    print(f"\n📍 العداد الحالي: {current} كم")
    print("=" * 72)
    for item in data:
        status = "🟥 مستحقة الآن" if item["remaining_km"] <= 0 else "🟩 ليست مستحقة"
        print(
            f"- {item['name']}: آخر تغيير {item['last_change_km']} كم | "
            f"دورية {item['interval_km']} كم | الاستحقاق {item['due_at_km']} كم | "
            f"المتبقي {item['remaining_km']} كم | {status}"
        )


def cmd_log_service(args: argparse.Namespace, store: TrackerStore) -> None:
    record = ServiceRecord(
        date=date_or_today(args.date),
        mileage_km=args.km,
        title=args.title,
        details=args.details or "",
        cost=args.cost,
    )
    store.add_service_record(record)
    print(f"✅ تم تسجيل صيانة '{args.title}' بتاريخ {record.date}")


def cmd_history(_: argparse.Namespace, store: TrackerStore) -> None:
    history = store.data.get("service_history", [])
    if not history:
        print("لا يوجد سجل صيانات حتى الآن.")
        return

    print("\n🛠️ سجل الصيانات:")
    print("=" * 72)
    for rec in history:
        cost_text = f"{rec['cost']:.2f}" if isinstance(rec.get("cost"), (int, float)) else rec.get("cost", 0)
        print(
            f"- {rec['date']} | {rec['mileage_km']} كم | {rec['title']} | "
            f"التكلفة: {cost_text} | التفاصيل: {rec.get('details', '')}"
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="برنامج لتتبع القطع الاستهلاكية وصيانة السيارة",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB_PATH,
        help="مسار ملف البيانات JSON (افتراضي: car_maintenance_data.json)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    set_mileage = sub.add_parser("set-mileage", help="تحديث العداد الحالي للسيارة")
    set_mileage.add_argument("km", type=positive_int)
    set_mileage.set_defaults(func=cmd_set_mileage)

    add_part = sub.add_parser("add-part", help="إضافة أو تحديث قطعة استهلاكية")
    add_part.add_argument("name", help="اسم القطعة")
    add_part.add_argument("interval", type=positive_int, help="المسافة بين كل تغيير وآخر")
    add_part.add_argument("last_change", type=positive_int, help="عداد الكيلومترات عند آخر تغيير")
    add_part.add_argument("--notes", default="", help="ملاحظات اختيارية")
    add_part.set_defaults(func=cmd_add_part)

    change_part = sub.add_parser("change-part", help="تسجيل تغيير قطعة موجودة")
    change_part.add_argument("name", help="اسم القطعة")
    change_part.add_argument("km", type=positive_int, help="العداد عند التغيير")
    change_part.add_argument("--notes", default="", help="ملاحظات اختيارية")
    change_part.set_defaults(func=cmd_change_part)

    due = sub.add_parser("due", help="عرض القطع المستحقة للتغيير")
    due.add_argument("--at-km", type=positive_int, default=None, help="احسب الاستحقاق عند عداد محدد")
    due.set_defaults(func=cmd_due)

    log_service = sub.add_parser("log-service", help="إضافة سجل صيانة")
    log_service.add_argument("title", help="عنوان الصيانة (مثال: تغيير زيت)")
    log_service.add_argument("km", type=positive_int, help="العداد وقت الصيانة")
    log_service.add_argument("--date", help="تاريخ الصيانة YYYY-MM-DD (الافتراضي اليوم)")
    log_service.add_argument("--details", default="", help="تفاصيل إضافية")
    log_service.add_argument("--cost", type=float, default=0.0, help="التكلفة")
    log_service.set_defaults(func=cmd_log_service)

    history = sub.add_parser("history", help="عرض سجل الصيانات")
    history.set_defaults(func=cmd_history)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    store = TrackerStore(args.db)
    args.func(args, store)


if __name__ == "__main__":
    main()
