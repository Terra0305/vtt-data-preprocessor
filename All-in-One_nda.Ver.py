import re
import os
import csv
import logging

# [Portfolio Note]
# 본 코드는 프로젝트 보안 규정(NDA) 준수를 위해, 
# 실제 데이터셋 명칭과 경로를 일반화(Generalization)하여 재구성한 버전입니다.

# 로깅 설정 (Logging Setup)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if not logger.handlers:
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    
    # 로그 파일도 일반적인 이름으로 변경
    log_filename = 'data_preprocessing.log' 
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

def load_typo_dictionary(csv_path: str) -> dict:
    """
    CSV 파일에서 오타 교정 사전을 로드합니다.
    (Load typo correction dictionary from CSV)
    """
    typo_dict = {}
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # CSV 컬럼명도 일반적인 형태로 가정
                typo_dict[row['typo']] = row['correction'] 
        logger.info(f"오타 사전 로드 완료: {len(typo_dict)}개 항목")
        return typo_dict
    except FileNotFoundError:
        logger.warning(f"오타 사전 파일을 찾을 수 없습니다: '{csv_path}'")
        return {}
    except Exception as e:
        logger.error(f"오타 사전 로드 중 오류: {e}")
        return {}

def apply_typo_corrections(text: str, typo_dict: dict) -> str:
    """
    텍스트에 오타 교정 사전을 적용합니다.
    """
    for typo, correction in typo_dict.items():
        text = text.replace(typo, correction)
    return text

def clean_vtt_file(input_path: str, output_path: str, typo_dict: dict):
    """
    VTT 파일을 읽어 사전 정의된 규칙(Regex, Dictionary)을 적용하여 정제합니다.
    """
    logger.info(f"Processing: '{os.path.basename(input_path)}'...")
    try:
        with open(input_path, 'r', encoding='utf-8') as infile, \
             open(output_path, 'w', encoding='utf-8') as outfile:
            
            for line in infile:
                # VTT 메타데이터(타임스탬프, 헤더 등)는 유지
                if "-->" in line or line.strip().isdigit() or "WEBVTT" in line or not line.strip():
                    outfile.write(line)
                    continue

                # 1. Regex: 괄호 및 내부 텍스트 제거 
                cleaned_line = re.sub(r'\[.*?\]|\(.*?\)', '', line)
                
                # 2. Regex: 불필요한 특수문자 제거 
                cleaned_line = re.sub(r'[#♪&]', '', cleaned_line)
                
                # 3. Dictionary: 오타 교정 적용 
                cleaned_line = apply_typo_corrections(cleaned_line, typo_dict)

                if cleaned_line.strip():
                    outfile.write(cleaned_line)

        logger.info(f"Done. Saved to: '{os.path.basename(output_path)}'")
        return True
    except FileNotFoundError:
        logger.error(f"File not found: '{input_path}'")
        return False
    except Exception as e:
        logger.error(f"Error processing '{input_path}': {e}")
        return False

def main():
    """
    메인 실행 함수
    """
    # [Configuration] 사용자 설정 변수
    # 실제 파일명 대신 플레이스홀더 사용
    TARGET_FILE_NAME = "sample_dataset_v01"  # {수정 가능한 대상 파일명}
    INPUT_DIR = "raw_data"                   # {입력 폴더 경로}
    OUTPUT_DIR = "cleaned_data"              # {출력 폴더 경로}
    TYPO_DICT_FILE = "typo_correction_rules.csv" 

    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        script_dir = os.getcwd()

    input_folder = os.path.join(script_dir, INPUT_DIR)
    output_folder = os.path.join(script_dir, OUTPUT_DIR)
    os.makedirs(output_folder, exist_ok=True)

    # 오타 사전 로드
    typo_csv_path = os.path.join(script_dir, TYPO_DICT_FILE)
    typo_dict = load_typo_dictionary(typo_csv_path)

    # 처리 대상 파일 목록 구성 (확장성 고려)
    files_to_process = {
        'en': os.path.join(input_folder, f'{TARGET_FILE_NAME}_en.vtt'),
        'kr': os.path.join(input_folder, f'{TARGET_FILE_NAME}_kr.vtt')
    }
    
    logger.info("="*50)
    logger.info(f"Target Dataset: {TARGET_FILE_NAME}")
    logger.info("Starting Batch Processing...")

    # 파일 존재 여부 확인 
    all_files_exist = True
    for lang, path in files_to_process.items():
        if not os.path.exists(path):
            logger.error(f"Input file missing: '{path}'")
            all_files_exist = False
    
    if not all_files_exist:
        logger.error("Required files are missing. Aborting process.")
        return

    # 배치 처리 실행 
    for lang, input_path in files_to_process.items():
        output_path = os.path.join(output_folder, f'{TARGET_FILE_NAME}_{lang}_CLEANED.vtt')
        clean_vtt_file(input_path, output_path, typo_dict)
    
    logger.info("-" * 30)
    logger.info("All tasks completed successfully.")
    logger.info(f"Output Directory: {output_folder}")
    logger.info("="*50)

if __name__ == "__main__":
    main()