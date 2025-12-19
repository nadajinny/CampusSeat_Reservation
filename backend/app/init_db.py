# app/db/init_db.py
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models, services
from app.constants import FacilityConstants  # [NEW] 상수 사용을 위해 import
from app.constants import ReservationLimits
def init_db_data(db: Session):
    """
    실제 DB 초기화 로직 (세션은 외부에서 주입받음)
    constants.py의 설정을 기반으로 데이터를 생성합니다.
    """
    try:
        # ---------------------------------------------------------
        # 1. 미팅룸 초기화 (FacilityConstants.MEETING_ROOM_IDS 사용)
        # ---------------------------------------------------------
        meeting_rooms_count = services.meeting_room_service.get_meeting_room_count(db)
        
        # [수정] DB가 비어있을 때 상수 목록에 있는 방들을 생성
        if meeting_rooms_count == 0:
            target_ids = FacilityConstants.MEETING_ROOM_IDS
            print(f"📝 Meeting rooms not found. Creating rooms: {target_ids}...")
            
            for room_id in target_ids:
                room = models.MeetingRoom(
                    room_id=room_id,
                    min_capacity=ReservationLimits.MEETING_ROOM_MIN_PARTICIPANTS,
                    max_capacity=ReservationLimits.MEETING_ROOM_MAX_PARTICIPANTS,
                )
                db.add(room)
            
            db.commit()
            print(f"✅ Created {len(target_ids)} meeting rooms.")
        
        # ---------------------------------------------------------
        # 2. 좌석 초기화 (SEAT_MIN_ID ~ SEAT_MAX_ID 사용)
        # ---------------------------------------------------------
        seats_count = services.seat_service.get_seats_count(db)
        
        if seats_count == 0:
            min_id = FacilityConstants.SEAT_MIN_ID
            max_id = FacilityConstants.SEAT_MAX_ID
            
            print(f"📝 Seats not found. Creating {min_id}-{max_id}...")
            
            # [수정] 하드코딩된 range(1, 71) 대신 상수를 사용하여 범위 설정
            for seat_id in range(min_id, max_id + 1):
                services.seat_service.create_seat(db, seat_id=seat_id)
            
            # create_seat 내부 로직에 따라 commit이 필요할 수 있음 (서비스 로직 확인 결과 commit 포함됨)
            # 안전을 위해 한 번 더 확인하거나 생략 가능. 여기서는 서비스가 개별 commit한다고 가정.
            print(f"✅ Created {max_id - min_id + 1} seats.")
            
    except Exception as e:
        print(f"❌ Error initializing data: {e}")
        db.rollback()

def initialize_data():
    """
    앱 시작 시 호출될 진입점 함수
    """
    with SessionLocal() as db:
        init_db_data(db)