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

  const selectAll = useStore(s => s.selectAll);
  const selectedRows = useStore(s => s.selectedRows);
  const toggleAll = useStore(s => s.toggleAll);
  const toggleRow = useStore(s => s.toggleRow);

  return (
    <main className={styles['page--cards']}>
      <Header title="Карточки паспортов" />

      <div className={`${styles['page__content']} ${styles['page__content--cards']}`}>
        <Stats />
        <PassportTable selectAll={selectAll} selectedRows={selectedRows} toggleAll={toggleAll} toggleRow={toggleRow} openExport={() => setShowModal(true)} />

        <Footer
          selectedCount={selectedRows.filter(Boolean).length}
          onDelete={() => { /* implement delete */ }}
          onReset={() => { /* implement reset */ }}
          onSave={() => setShowModal(true)}
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
              <p>Будет экспортировано: <strong>{selectedRows.filter(Boolean).length} паспорта</strong></p>
              <label className={styles['export-modal__option']}><input type="checkbox" /> Удалить экспортируемые паспорта</label>
            </div>
            <div className={styles['export-modal__footer']}>
              <button onClick={() => setShowModal(false)} className={styles['cards__btn']}>Отмена</button>
              <button onClick={() => setShowModal(false)} className={`${styles['cards__btn']} ${styles['cards__btn--save']}`}>Скачать .xlsx</button>
            </div>
          </div>
        </Modal>
      )}
    </main>
  );
};

export default PassportCards;
