# app/db/init_db.py
from sqlalchemy.orm import Session
from app.database import SessionLocal # 프로젝트 구조에 맞게 수정
from app import models, services # service, models 경로에 맞게 수정
# (필요한 service, model import)

def init_db_data(db: Session):
    """
    실제 DB 초기화 로직 (세션은 외부에서 주입받음)
    """
    try:
        # 1. 미팅룸 초기화 (1-3번)
        meeting_rooms_count = services.meeting_room_service.get_meeting_room_count(db)
        if meeting_rooms_count == 0:
            print("📝 Meeting rooms not found. Creating 1-3...")
            for room_id in range(1, 4):
                room = models.MeetingRoom(
                    room_id=room_id,
                    min_capacity=3,
                    max_capacity=6
                )
                db.add(room)
            db.commit()
            print("✅ Created 3 meeting rooms.")
        
        # 2. 좌석 초기화 (1-70번)
        seats_count = services.seat_service.get_seats_count(db)
        if seats_count == 0:
            print("📝 Seats not found. Creating 1-70...")
            for seat_id in range(1, 71):
                services.seat_service.create_seat(db, seat_id=seat_id)
            # create_seat 내부에서 commit을 안 한다면 여기서 db.commit() 필요
            print("✅ Created 70 seats.")
            
    except Exception as e:
        print(f"❌ Error initializing data: {e}")
        db.rollback()

def initialize_data():
    """
    앱 시작 시 호출될 진입점 함수
    """
    with SessionLocal() as db:
        init_db_data(db)