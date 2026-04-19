import React, { useState } from 'react';
import Header from '@/components/layout/Header';
import useStore from '@/store/useStore';
import Modal from '@/components/shared/Modal';
import Stats from '@/components/features/passport/Stats';
import PassportTable from '@/components/features/passport/PassportTable';
import Footer from '@/components/features/passport/Footer';
import styles from './PassportCards.module.scss';

const PassportCards: React.FC = () => {
  const [showModal, setShowModal] = useState(false);
  const [confirmAction, setConfirmAction] = useState<null | 'delete' | 'reset'>(null);
  const [removeAfterExport, setRemoveAfterExport] = useState(false);

  const selectedIds = useStore((s) => s.selectedIds);
  const isExporting = useStore((s) => s.isExporting);
  const exportError = useStore((s) => s.exportError);

  const performDelete = useStore((s) => s.deleteSelected);
  const performReset = useStore((s) => s.resetSelected);
  const exportSelectedToExcel = useStore((s) => s.exportSelectedToExcel);
  const clearExportError = useStore((s) => s.clearExportError);

  const openDeleteConfirm = () => setConfirmAction('delete');
  const openResetConfirm = () => setConfirmAction('reset');
  const closeConfirm = () => setConfirmAction(null);

  const onConfirm = () => {
    if (confirmAction === 'delete') performDelete();
    if (confirmAction === 'reset') performReset();
    closeConfirm();
  };

  const openExportModal = () => {
    clearExportError();
    setRemoveAfterExport(false);
    setShowModal(true);
  };

  const handleExport = async () => {
    await exportSelectedToExcel(removeAfterExport);
    if (!useStore.getState().exportError) {
      setShowModal(false);
      setRemoveAfterExport(false);
    }
  };

  return (
    <main className={styles['page--cards']}>
      <Header title="Карточки паспортов" />

      <div className={`${styles['page__content']} ${styles['page__content--cards']}`}>
        <Stats />
        <PassportTable />

        <Footer
          selectedCount={selectedIds.length}
          onDelete={openDeleteConfirm}
          onReset={openResetConfirm}
          onSave={openExportModal}
        />
      </div>

      {showModal && (
        <Modal onClose={() => setShowModal(false)}>
          <div className={styles['export-modal']}>
            <div className={styles['export-modal__header']}>
              <h3>Экспорт в Excel</h3>
              <button onClick={() => setShowModal(false)} className={styles['export-modal__close']}><span className="material-symbols-outlined">close</span></button>
            </div>
            <div className={styles['export-modal__body']}>
              <p>Будет экспортировано: <strong>{selectedIds.length} паспорта</strong></p>
              <label className={styles['export-modal__option']}>
                <input
                  type="checkbox"
                  checked={removeAfterExport}
                  onChange={(e) => setRemoveAfterExport(e.target.checked)}
                />
                Удалить экспортируемые паспорта
              </label>
              {exportError && <p className={styles['export-modal__error']}>{exportError}</p>}
            </div>
            <div className={styles['export-modal__footer']}>
              <button onClick={() => setShowModal(false)} className={styles['cards__btn']}>Отмена</button>
              <button
                onClick={handleExport}
                disabled={isExporting || selectedIds.length === 0}
                className={`${styles['cards__btn']} ${styles['cards__btn--save']}`}
              >
                {isExporting ? 'Экспорт...' : 'Скачать .xlsx'}
              </button>
            </div>
          </div>
        </Modal>
      )}

      {confirmAction && (
        <Modal onClose={closeConfirm}>
          <div className={styles['export-modal']}>
            <div className={styles['export-modal__header']}>
              <h3>{confirmAction === 'delete' ? 'Удалить выбранные' : 'Сбросить изменения'}</h3>
              <button onClick={closeConfirm} className={styles['export-modal__close']}><span className="material-symbols-outlined">close</span></button>
            </div>
            <div className={styles['export-modal__body']}>
              <p>
                {confirmAction === 'delete'
                  ? `Вы действительно хотите удалить ${selectedIds.length} выбранных записей? Это действие нельзя отменить.`
                  : `Вы действительно хотите сбросить изменения для ${selectedIds.length} выбранных записей? Изменения будут потеряны.`}
              </p>
            </div>
            <div className={styles['export-modal__footer']}>
              <button onClick={closeConfirm} className={styles['cards__btn']}>Отмена</button>
              <button onClick={() => { onConfirm(); }} className={`${styles['cards__btn']} ${styles['cards__btn--delete']}`}>Подтвердить</button>
            </div>
          </div>
        </Modal>
      )}
    </main>
  );
};

export default PassportCards;
