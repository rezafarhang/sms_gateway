import logging
import httpx
import asyncio
from typing import Optional, Tuple
from config.operator_config import OPERATORS, OperatorConfig

logger = logging.getLogger(__name__)


class OperatorClient:
    @staticmethod
    async def _send_with_backoff(
        operator: OperatorConfig,
        phone_number: str,
        message: str,
        max_retries: int = 3
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Send SMS to operator with exponential backoff retry.
        Backoff: 1s, 2s, 4s
        """
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=operator.timeout) as client:
                    response = await client.post(
                        operator.url,
                        json={
                            "phone_number": phone_number,
                            "message": message
                        }
                    )

                    if response.status_code == 200:
                        data = response.json()
                        if data.get("status") == "sent":
                            return True, data.get("message_id"), None
                        else:
                            # Operator returned failure status (not retryable)
                            error = data.get("error", "Unknown error")
                            logger.warning(f"Operator {operator.name} failed: {error}")
                            return False, None, error
                    else:
                        # HTTP error, retry with backoff
                        logger.warning(f"Operator {operator.name} HTTP {response.status_code}, attempt {attempt + 1}/{max_retries}")
                        if attempt < max_retries - 1:
                            backoff_time = 2 ** attempt  # 1s, 2s, 4s
                            await asyncio.sleep(backoff_time)
                            continue
                        else:
                            return False, None, f"HTTP error {response.status_code}"

            except Exception as e:
                # Network/timeout error, retry with backoff
                logger.warning(f"Operator {operator.name} exception: {str(e)}, attempt {attempt + 1}/{max_retries}")
                if attempt < max_retries - 1:
                    backoff_time = 2 ** attempt  # 1s, 2s, 4s
                    await asyncio.sleep(backoff_time)
                    continue
                else:
                    return False, None, str(e)

        return False, None, "Max retries exceeded"

    @staticmethod
    async def send_sms(phone_number: str, message: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Send SMS through operators with failover.
        Each operator is retried 3 times with exponential backoff before moving to next.
        Returns: (success: bool, message_id: str|None, error: str|None)
        """
        for operator in sorted(OPERATORS, key=lambda x: x.priority):
            logger.info(f"Trying operator {operator.name} (priority {operator.priority})")
            success, message_id, error = await OperatorClient._send_with_backoff(
                operator, phone_number, message
            )

            if success:
                logger.info(f"SMS sent via {operator.name}, message_id: {message_id}")
                return True, message_id, None
            else:
                logger.warning(f"Operator {operator.name} failed: {error}, trying next operator")
                continue

        # All operators failed
        return False, None, "All operators failed after retries"
