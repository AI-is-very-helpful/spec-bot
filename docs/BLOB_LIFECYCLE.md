# Azure Blob Storage Lifecycle Management

## Overview

Blob Storage에 저장된 ZIP 파일은 24시간 후 만료되는 SAS URL을 통해 다운로드할 수 있습니다. 또한 Azure Blob Lifecycle Management를 통해 오래된 파일이 자동으로 삭제되도록 설정할 수 있습니다.

## Lifecycle Policy Configuration

Azure Portal 또는 CLI로 Lifecycle Management 정책을 설정할 수 있습니다.

### Azure Portal에서 설정

1. **Storage Account** 선택
2. **Data management** → **Lifecycle management** 이동
3. **Add a rule** 클릭

### Policy JSON

```json
{
  "rules": [
    {
      "name": "delete-spec-bot-zip-files",
      "enabled": true,
      "type": "Lifecycle",
      "definition": {
        "filters": {
          "blobTypes": ["blockBlob"],
          "prefixMatch": ["spec-bot-documents/"]
        },
        "actions": {
          "baseBlob": {
            "delete": {
              "daysAfterModificationGreaterThan": 1
            }
          }
        }
      }
    }
  ]
}
```

### Azure CLI로 설정

```bash
# Resource group 및 storage account 이름 설정
RG_NAME="your-resource-group"
STORAGE_NAME="your-storage-account"

# Lifecycle policy 적용
az storage account management-policy create \
  --resource-group $RG_NAME \
  --storage-account $STORAGE_NAME \
  --policy '@policy.json'
```

## 동작 방식

1. ZIP 파일이 Blob Storage에 업로드됨
2. 24시간 유효한 SAS URL 생성
3. 사용자가 SAS URL로 ZIP 다운로드
4. 1일 후 Azure가 자동으로 ZIP 파일 삭제

## 보안 고려사항

- **SAS URL**: 24시간 후 만료 (재발급 불가)
- **자동 삭제**: 1일 후 Lifecycle Policy가 파일 삭제
- **소스 코드**: 외부 DB에 저장되지 않음 (메모리에서만 처리)
