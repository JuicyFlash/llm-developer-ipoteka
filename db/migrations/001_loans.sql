CREATE TABLE clients (
    id          bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    full_name   text NOT NULL
);

CREATE TABLE loans (
    id           bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    client_id    bigint NOT NULL REFERENCES clients(id),
    principal    bigint NOT NULL CHECK (principal > 0),
    rate_bp      integer NOT NULL CHECK (rate_bp >= 0),
    term_months  integer NOT NULL CHECK (term_months > 0),
    issued_on    date NOT NULL,
    payment_day  smallint NOT NULL CHECK (payment_day BETWEEN 1 AND 28)
);

INSERT INTO clients (full_name) VALUES
    ('Иванов Петр Сергеевич'), ('Смирнова Анна Олеговна'), ('Кузнецов Илья Андреевич'),
    ('Попова Мария Викторовна'), ('Соколов Дмитрий Ильич');

INSERT INTO loans (client_id, principal, rate_bp, term_months, issued_on, payment_day) VALUES
    (1, 500000000, 1200, 240, '2025-10-15', 15),
    (2, 320000000, 600, 360, '2024-03-01', 1),
    (3, 750000000, 1850, 180, '2025-06-10', 10),
    (4, 180000000, 990, 120, '2023-12-20', 20),
    (5, 1200000000, 1450, 300, '2026-01-28', 28);
