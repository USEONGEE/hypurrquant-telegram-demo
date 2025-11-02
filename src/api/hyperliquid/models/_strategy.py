from pydantic import BaseModel, Field
from typing import Dict, Optional


class ParamConfig(BaseModel):
    """
    단일 파라미터에 대한 설정.
    예: {
      "default": 0.2,
      "min": 0,
      "max": 1,
      "label": "모멘텀 퍼센트",
      "description": "주가 상승 모멘텀을 측정하는 지표..."
    }
    """

    default: float = Field(..., description="기본값")
    min: float = Field(..., description="허용 최소값")
    max: float = Field(..., description="허용 최대값")
    label: str = Field(..., description="사용자에게 표시될 파라미터 이름")
    description: Optional[str] = Field("", description="파라미터에 대한 설명")


class StrategyMeta(BaseModel):
    """
    서버에서 받아오는 '전략' 정보 전용 모델
    """

    name: str
    endpoint: str
    default_params: Dict[str, ParamConfig]

    def update_params(self, override_dict: Optional[dict]):
        """
        override_dict: 예) {"momentum_pct": 0.5, "volume_pct": 30}
        - 사용자가 입력한 override 값들이 들어옴
        - 이 값들을 default_params[해당키].default 에 반영
        - min~max 범위 밖이면 ValueError 발생 (선택적으로 처리)
        """
        if not override_dict:
            return

        for param_key, param_config in self.default_params.items():
            if param_key in override_dict:
                user_val = override_dict[param_key]
                # 사용자가 입력한 값이 min/max 범위를 벗어나면 예외 발생시키거나
                # 적절히 핸들링하면 됨
                if not (param_config.min <= user_val <= param_config.max):
                    raise ValueError(
                        f"Parameter '{param_key}' must be in range "
                        f"[{param_config.min}, {param_config.max}], but got {user_val}"
                    )
                # 범위 내라면 default값에 반영
                param_config.default = user_val
