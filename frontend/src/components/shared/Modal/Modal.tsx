import React from 'react';
import styles from './Modal.module.scss';

type ModalProps = {
  children: React.ReactNode;
  onClose?: () => void;
};

const Modal: React.FC<ModalProps> = ({ children, onClose }) => {
  return (
    <div className={styles.modal} role="dialog" aria-modal="true">
      <div className={styles['modal__backdrop']} onClick={onClose} />
      <div className={styles['modal__sheet']}>
        {children}
      </div>
    </div>
  );
};

export default Modal;
