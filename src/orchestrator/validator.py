"""
Validation and testing for generated applications.

Provides API, UI, and downtime validation capabilities.
"""

import requests
import time
import threading
from typing import Dict, List, Tuple, Optional
from src.utils.logger import get_logger

logger = get_logger(__name__, component="validator")


class Validator:
    """Validates generated application functionality."""
    
    def __init__(self, api_base_url: str, ui_base_url: str, run_id: str):
        """
        Initialize validator.
        
        Args:
            api_base_url: Base URL for API (e.g., http://localhost:8000)
            ui_base_url: Base URL for UI (e.g., http://localhost:3000)
            run_id: Run identifier for logging
        """
        self.api_base_url = api_base_url.rstrip('/')
        self.ui_base_url = ui_base_url.rstrip('/')
        self.run_id = run_id
        self.downtime_count = 0
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        
    def test_crud_endpoints(self) -> Tuple[int, float]:
        """
        Test CRUD operations for Student, Course, Teacher entities.
        
        Returns:
            Tuple of (crude_score, esr) where:
                crude_score: 0-12 (4 ops × 3 entities)
                esr: Endpoint success rate 0-1
        """
        successful_ops = 0
        total_ops = 12  # 4 CRUD operations × 3 entities
        
        entities = ['students', 'courses', 'teachers']
        test_data = {
            'students': {'name': 'Test Student', 'email': 'test@example.com', 
                        'enrollment_date': '2025-01-01'},
            'courses': {'code': 'CS101', 'title': 'Intro to CS', 'credits': 3},
            'teachers': {'name': 'Dr. Smith', 'email': 'smith@example.com', 
                        'department': 'Computer Science'}
        }
        
        created_ids: Dict[str, Optional[int]] = {}
        
        for entity in entities:
            # CREATE (POST)
            try:
                response = requests.post(
                    f"{self.api_base_url}/{entity}",
                    json=test_data[entity],
                    timeout=10
                )
                if response.status_code in [200, 201]:
                    successful_ops += 1
                    created_ids[entity] = response.json().get('id')
                    logger.debug(f"POST /{entity} succeeded", 
                               extra={'run_id': self.run_id})
            except Exception as e:
                logger.warning(f"POST /{entity} failed: {e}",
                             extra={'run_id': self.run_id})
                created_ids[entity] = None
                
        for entity in entities:
            entity_id = created_ids.get(entity)
            
            # READ (GET)
            try:
                if entity_id:
                    response = requests.get(
                        f"{self.api_base_url}/{entity}/{entity_id}",
                        timeout=10
                    )
                else:
                    response = requests.get(
                        f"{self.api_base_url}/{entity}",
                        timeout=10
                    )
                    
                if response.status_code == 200:
                    successful_ops += 1
                    logger.debug(f"GET /{entity} succeeded",
                               extra={'run_id': self.run_id})
            except Exception as e:
                logger.warning(f"GET /{entity} failed: {e}",
                             extra={'run_id': self.run_id})
                
            # UPDATE (PATCH)
            if entity_id:
                try:
                    update_data = {'name': 'Updated Name'} if entity != 'courses' else {'title': 'Updated Title'}
                    response = requests.patch(
                        f"{self.api_base_url}/{entity}/{entity_id}",
                        json=update_data,
                        timeout=10
                    )
                    if response.status_code == 200:
                        successful_ops += 1
                        logger.debug(f"PATCH /{entity}/{entity_id} succeeded",
                                   extra={'run_id': self.run_id})
                except Exception as e:
                    logger.warning(f"PATCH /{entity}/{entity_id} failed: {e}",
                                 extra={'run_id': self.run_id})
                    
            # DELETE
            if entity_id:
                try:
                    response = requests.delete(
                        f"{self.api_base_url}/{entity}/{entity_id}",
                        timeout=10
                    )
                    if response.status_code in [200, 204]:
                        successful_ops += 1
                        logger.debug(f"DELETE /{entity}/{entity_id} succeeded",
                                   extra={'run_id': self.run_id})
                except Exception as e:
                    logger.warning(f"DELETE /{entity}/{entity_id} failed: {e}",
                                 extra={'run_id': self.run_id})
                    
        crude_score = successful_ops
        esr = successful_ops / total_ops if total_ops > 0 else 0.0
        
        logger.info(f"CRUD validation complete: {successful_ops}/{total_ops} operations succeeded",
                   extra={'run_id': self.run_id, 'metadata': {
                       'CRUDe': crude_score, 'ESR': esr
                   }})
        
        return crude_score, esr
        
    def test_relational_endpoints(self) -> int:
        """
        Test relational endpoints (enrollments, teacher assignments).
        
        Returns:
            Number of successful relational operations
        """
        successful = 0
        
        # Test enrollment endpoints
        try:
            response = requests.get(f"{self.api_base_url}/enrollments", timeout=10)
            if response.status_code == 200:
                successful += 1
        except Exception:
            pass
            
        return successful
        
    def test_ui_pages(self) -> int:
        """
        Test UI page accessibility and content.
        
        Returns:
            Number of accessible pages
        """
        pages = ['/', '/students', '/courses', '/teachers', '/enrollments']
        accessible_count = 0
        
        for page in pages:
            try:
                response = requests.get(f"{self.ui_base_url}{page}", timeout=10)
                if response.status_code == 200 and len(response.text) > 0:
                    accessible_count += 1
                    logger.debug(f"UI page {page} accessible",
                               extra={'run_id': self.run_id})
            except Exception as e:
                logger.warning(f"UI page {page} not accessible: {e}",
                             extra={'run_id': self.run_id})
                             
        logger.info(f"UI validation complete: {accessible_count}/{len(pages)} pages accessible",
                   extra={'run_id': self.run_id})
                   
        return accessible_count
        
    def health_check(self) -> bool:
        """
        Check if both API and UI are responding.
        
        Returns:
            True if both return HTTP 200, False otherwise
        """
        try:
            api_response = requests.get(f"{self.api_base_url}/", timeout=5)
            ui_response = requests.get(f"{self.ui_base_url}/", timeout=5)
            return api_response.status_code == 200 and ui_response.status_code == 200
        except Exception:
            return False
            
    def start_downtime_monitoring(self, interval_seconds: int = 5) -> None:
        """
        Start monitoring for downtime incidents.
        
        Args:
            interval_seconds: Check interval (default 5 seconds)
        """
        self.monitoring = True
        self.downtime_count = 0
        
        def monitor():
            while self.monitoring:
                if not self.health_check():
                    self.downtime_count += 1
                    logger.warning("Downtime detected",
                                 extra={'run_id': self.run_id, 
                                       'event': 'downtime',
                                       'metadata': {'zdi_count': self.downtime_count}})
                time.sleep(interval_seconds)
                
        self.monitor_thread = threading.Thread(target=monitor, daemon=True)
        self.monitor_thread.start()
        logger.info("Downtime monitoring started",
                   extra={'run_id': self.run_id, 'event': 'monitoring_start'})
        
    def stop_downtime_monitoring(self) -> int:
        """
        Stop downtime monitoring and return incident count.
        
        Returns:
            Total downtime incidents detected (ZDI)
        """
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=10)
            
        logger.info(f"Downtime monitoring stopped. Total incidents: {self.downtime_count}",
                   extra={'run_id': self.run_id, 'event': 'monitoring_stop',
                         'metadata': {'ZDI': self.downtime_count}})
                         
        return self.downtime_count
        
    def compute_migration_continuity(self) -> float:
        """
        Compute migration continuity metric.
        
        MC = 1 if no downtime during migrations, 0 otherwise.
        
        Returns:
            Migration continuity score (0-1)
        """
        # Simplified: MC = 1 if ZDI == 0, else 0
        # Could be enhanced to track downtime during specific migration steps
        return 1.0 if self.downtime_count == 0 else 0.0
