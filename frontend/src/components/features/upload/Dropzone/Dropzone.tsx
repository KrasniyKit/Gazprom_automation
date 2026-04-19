import React, { useRef, useState } from 'react';
import styles from './Dropzone.module.scss';
import useStore from '@/store/useStore';

const Dropzone: React.FC = () => {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);

  const uploadFiles = useStore((s) => s.uploadFiles);
  const isUploading = useStore((s) => s.isUploading);
  const uploadError = useStore((s) => s.uploadError);
  const clearUploadError = useStore((s) => s.clearUploadError);

  const processFiles = async (fileList: FileList | null) => {
    if (!fileList?.length) return;

    clearUploadError();
    setValidationError(null);

    const files = Array.from(fileList);
    const invalid = files.find((f) => !f.name.toLowerCase().endsWith('.pdf'));
    if (invalid) {
      setValidationError('Разрешены только PDF файлы.');
      return;
    }

    await uploadFiles(files);
  };

  return (
    <div
      className={`${styles.dropzone} ${isDragging ? styles['dropzone--dragging'] : ''}`.trim()}
      role="button"
      tabIndex={0}
      onClick={() => inputRef.current?.click()}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          inputRef.current?.click();
        }
      }}
      onDragOver={(e) => {
        e.preventDefault();
        setIsDragging(true);
      }}
      onDragLeave={(e) => {
        e.preventDefault();
        setIsDragging(false);
      }}
      onDrop={async (e) => {
        e.preventDefault();
        setIsDragging(false);
        await processFiles(e.dataTransfer.files);
      }}
    >
      <input
        ref={inputRef}
        type="file"
        multiple
        accept=".pdf,application/pdf"
        className={styles['dropzone__input']}
        onChange={async (e) => {
          const input = e.currentTarget;
          const selectedFiles = input.files;
          await processFiles(selectedFiles);
          input.value = '';
        }}
      />
      <span className={`material-symbols-outlined ${styles['dropzone__icon']}`}>upload</span>
      <p className={styles['dropzone__text']}>Перетащите PDF файлы сюда</p>
      <p className={styles['dropzone__or']}>или</p>
      <button type="button" className={styles['dropzone__btn']} disabled={isUploading}>
        {isUploading ? 'Загрузка...' : 'Выбрать файлы'}
      </button>
      <p className={styles['dropzone__hint']}>Максимальный размер файла задается backend.</p>
      {(validationError || uploadError) && (
        <p className={styles['dropzone__error']}>{validationError ?? uploadError}</p>
      )}
    </div>
  );
};

export default Dropzone;
