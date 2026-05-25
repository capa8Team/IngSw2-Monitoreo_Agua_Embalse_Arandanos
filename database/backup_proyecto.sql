--
-- PostgreSQL database dump
--

\restrict W893PrVcqzLZ5ZVgZSzZll4rVMnO4fpZrHG44wZQuKwAQ8uVRFCPrzQ0b6nwfCD

-- Dumped from database version 18.3
-- Dumped by pg_dump version 18.3

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alertas; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.alertas (
    id_alerta integer NOT NULL,
    id_usuario integer NOT NULL,
    mensaje text NOT NULL,
    nivel_critico character varying(20) DEFAULT 'info'::character varying,
    leida boolean DEFAULT false,
    fecha_generacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.alertas OWNER TO postgres;

--
-- Name: alertas_id_alerta_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.alertas_id_alerta_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.alertas_id_alerta_seq OWNER TO postgres;

--
-- Name: alertas_id_alerta_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.alertas_id_alerta_seq OWNED BY public.alertas.id_alerta;


--
-- Name: dashboards; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.dashboards (
    id_dashboard integer NOT NULL,
    id_usuario integer NOT NULL,
    ultima_actualizacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.dashboards OWNER TO postgres;

--
-- Name: dashboards_id_dashboard_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.dashboards_id_dashboard_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.dashboards_id_dashboard_seq OWNER TO postgres;

--
-- Name: dashboards_id_dashboard_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.dashboards_id_dashboard_seq OWNED BY public.dashboards.id_dashboard;


--
-- Name: dispositivos; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.dispositivos (
    id_dispositivo integer NOT NULL,
    nombre_dispositivo character varying(100),
    ubicacion text,
    id_arduino_hardware character varying(50),
    sector character varying(100),
    estado_bateria integer DEFAULT 100,
    estado_funcional boolean DEFAULT true
);


ALTER TABLE public.dispositivos OWNER TO postgres;

--
-- Name: dispositivos_id_dispositivo_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.dispositivos_id_dispositivo_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.dispositivos_id_dispositivo_seq OWNER TO postgres;

--
-- Name: dispositivos_id_dispositivo_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.dispositivos_id_dispositivo_seq OWNED BY public.dispositivos.id_dispositivo;


--
-- Name: intervalos_alerta; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.intervalos_alerta (
    id_intervalo integer NOT NULL,
    etiqueta text NOT NULL,
    valor_minimo numeric,
    valor_maximo numeric,
    editado_por integer,
    fecha_modificacion timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    id_dispositivo integer
);


ALTER TABLE public.intervalos_alerta OWNER TO postgres;

--
-- Name: intervalos_alerta_id_intervalo_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.intervalos_alerta_id_intervalo_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.intervalos_alerta_id_intervalo_seq OWNER TO postgres;

--
-- Name: intervalos_alerta_id_intervalo_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.intervalos_alerta_id_intervalo_seq OWNED BY public.intervalos_alerta.id_intervalo;


--
-- Name: roles; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.roles (
    id_rol integer NOT NULL,
    nombre_rol character varying(50) NOT NULL
);


ALTER TABLE public.roles OWNER TO postgres;

--
-- Name: roles_id_rol_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.roles_id_rol_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.roles_id_rol_seq OWNER TO postgres;

--
-- Name: roles_id_rol_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.roles_id_rol_seq OWNED BY public.roles.id_rol;


--
-- Name: sensores; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.sensores (
    id_sensor integer NOT NULL,
    id_dispositivo integer,
    tipo_sensor character varying(50)
);


ALTER TABLE public.sensores OWNER TO postgres;

--
-- Name: sensores_id_sensor_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.sensores_id_sensor_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.sensores_id_sensor_seq OWNER TO postgres;

--
-- Name: sensores_id_sensor_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.sensores_id_sensor_seq OWNED BY public.sensores.id_sensor;


--
-- Name: usuarios; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.usuarios (
    id_usuario integer NOT NULL,
    nombre text NOT NULL,
    email text NOT NULL,
    password_hash text NOT NULL,
    id_rol integer NOT NULL
);


ALTER TABLE public.usuarios OWNER TO postgres;

--
-- Name: usuarios_id_usuario_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.usuarios_id_usuario_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.usuarios_id_usuario_seq OWNER TO postgres;

--
-- Name: usuarios_id_usuario_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.usuarios_id_usuario_seq OWNED BY public.usuarios.id_usuario;


--
-- Name: alertas id_alerta; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alertas ALTER COLUMN id_alerta SET DEFAULT nextval('public.alertas_id_alerta_seq'::regclass);


--
-- Name: dashboards id_dashboard; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dashboards ALTER COLUMN id_dashboard SET DEFAULT nextval('public.dashboards_id_dashboard_seq'::regclass);


--
-- Name: dispositivos id_dispositivo; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dispositivos ALTER COLUMN id_dispositivo SET DEFAULT nextval('public.dispositivos_id_dispositivo_seq'::regclass);


--
-- Name: intervalos_alerta id_intervalo; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.intervalos_alerta ALTER COLUMN id_intervalo SET DEFAULT nextval('public.intervalos_alerta_id_intervalo_seq'::regclass);


--
-- Name: roles id_rol; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.roles ALTER COLUMN id_rol SET DEFAULT nextval('public.roles_id_rol_seq'::regclass);


--
-- Name: sensores id_sensor; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sensores ALTER COLUMN id_sensor SET DEFAULT nextval('public.sensores_id_sensor_seq'::regclass);


--
-- Name: usuarios id_usuario; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuarios ALTER COLUMN id_usuario SET DEFAULT nextval('public.usuarios_id_usuario_seq'::regclass);


--
-- Data for Name: alertas; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.alertas (id_alerta, id_usuario, mensaje, nivel_critico, leida, fecha_generacion) FROM stdin;
\.


--
-- Data for Name: dashboards; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.dashboards (id_dashboard, id_usuario, ultima_actualizacion) FROM stdin;
\.


--
-- Data for Name: dispositivos; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.dispositivos (id_dispositivo, nombre_dispositivo, ubicacion, id_arduino_hardware, sector, estado_bateria, estado_funcional) FROM stdin;
\.


--
-- Data for Name: intervalos_alerta; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.intervalos_alerta (id_intervalo, etiqueta, valor_minimo, valor_maximo, editado_por, fecha_modificacion, id_dispositivo) FROM stdin;
\.


--
-- Data for Name: roles; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.roles (id_rol, nombre_rol) FROM stdin;
1	Administrador
2	Cliente
\.


--
-- Data for Name: sensores; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.sensores (id_sensor, id_dispositivo, tipo_sensor) FROM stdin;
\.


--
-- Data for Name: usuarios; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.usuarios (id_usuario, nombre, email, password_hash, id_rol) FROM stdin;
\.


--
-- Name: alertas_id_alerta_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.alertas_id_alerta_seq', 1, false);


--
-- Name: dashboards_id_dashboard_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.dashboards_id_dashboard_seq', 1, false);


--
-- Name: dispositivos_id_dispositivo_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.dispositivos_id_dispositivo_seq', 1, false);


--
-- Name: intervalos_alerta_id_intervalo_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.intervalos_alerta_id_intervalo_seq', 1, false);


--
-- Name: roles_id_rol_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.roles_id_rol_seq', 2, true);


--
-- Name: sensores_id_sensor_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.sensores_id_sensor_seq', 1, false);


--
-- Name: usuarios_id_usuario_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.usuarios_id_usuario_seq', 1, false);


--
-- Name: alertas alertas_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alertas
    ADD CONSTRAINT alertas_pkey PRIMARY KEY (id_alerta);


--
-- Name: dashboards dashboards_id_usuario_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dashboards
    ADD CONSTRAINT dashboards_id_usuario_key UNIQUE (id_usuario);


--
-- Name: dashboards dashboards_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dashboards
    ADD CONSTRAINT dashboards_pkey PRIMARY KEY (id_dashboard);


--
-- Name: dispositivos dispositivos_id_arduino_hardware_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dispositivos
    ADD CONSTRAINT dispositivos_id_arduino_hardware_key UNIQUE (id_arduino_hardware);


--
-- Name: dispositivos dispositivos_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dispositivos
    ADD CONSTRAINT dispositivos_pkey PRIMARY KEY (id_dispositivo);


--
-- Name: intervalos_alerta intervalos_alerta_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.intervalos_alerta
    ADD CONSTRAINT intervalos_alerta_pkey PRIMARY KEY (id_intervalo);


--
-- Name: roles roles_nombre_rol_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_nombre_rol_key UNIQUE (nombre_rol);


--
-- Name: roles roles_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_pkey PRIMARY KEY (id_rol);


--
-- Name: sensores sensores_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sensores
    ADD CONSTRAINT sensores_pkey PRIMARY KEY (id_sensor);


--
-- Name: usuarios usuarios_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT usuarios_pkey PRIMARY KEY (id_usuario);


--
-- Name: idx_usuarios_email_lower; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX idx_usuarios_email_lower ON public.usuarios USING btree (lower(email));


--
-- Name: intervalos_alerta fk_admin_editor; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.intervalos_alerta
    ADD CONSTRAINT fk_admin_editor FOREIGN KEY (editado_por) REFERENCES public.usuarios(id_usuario);


--
-- Name: usuarios fk_rol; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.usuarios
    ADD CONSTRAINT fk_rol FOREIGN KEY (id_rol) REFERENCES public.roles(id_rol) ON DELETE RESTRICT;


--
-- Name: alertas fk_usuario_alerta; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alertas
    ADD CONSTRAINT fk_usuario_alerta FOREIGN KEY (id_usuario) REFERENCES public.usuarios(id_usuario) ON DELETE CASCADE;


--
-- Name: dashboards fk_usuario_dash; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.dashboards
    ADD CONSTRAINT fk_usuario_dash FOREIGN KEY (id_usuario) REFERENCES public.usuarios(id_usuario) ON DELETE CASCADE;


--
-- Name: intervalos_alerta intervalos_alerta_id_dispositivo_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.intervalos_alerta
    ADD CONSTRAINT intervalos_alerta_id_dispositivo_fkey FOREIGN KEY (id_dispositivo) REFERENCES public.dispositivos(id_dispositivo) ON DELETE CASCADE;


--
-- Name: sensores sensores_id_dispositivo_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sensores
    ADD CONSTRAINT sensores_id_dispositivo_fkey FOREIGN KEY (id_dispositivo) REFERENCES public.dispositivos(id_dispositivo);


--
-- PostgreSQL database dump complete
--

\unrestrict W893PrVcqzLZ5ZVgZSzZll4rVMnO4fpZrHG44wZQuKwAQ8uVRFCPrzQ0b6nwfCD

