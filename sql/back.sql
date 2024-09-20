--
-- PostgreSQL database dump
--

-- Dumped from database version 16.3
-- Dumped by pg_dump version 16.3

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
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
-- Name: events; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.events (
    id integer NOT NULL,
    internal_name character varying(255) NOT NULL,
    template_id integer,
    user_id integer,
    date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    address_country character varying(100),
    address_city character varying(100),
    address_line character varying(255),
    display_name character varying(255),
    hall_name character varying(255),
    unique_domain character varying(255),
    is_deleted boolean DEFAULT false
);


ALTER TABLE public.events OWNER TO postgres;

--
-- Name: invitation; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.invitation (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    event_id integer NOT NULL,
    with_spouse boolean NOT NULL,
    hash character varying(255) NOT NULL,
    accepted boolean
);


ALTER TABLE public.invitation OWNER TO postgres;

--
-- Name: new_table_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.new_table_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.new_table_id_seq OWNER TO postgres;

--
-- Name: new_table_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.new_table_id_seq OWNED BY public.invitation.id;


--
-- Name: templates; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.templates (
    id integer NOT NULL,
    displayname character varying(255) NOT NULL,
    viewname character varying(255) NOT NULL,
    type character varying(100) NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.templates OWNER TO postgres;

--
-- Name: templates_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.templates_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.templates_id_seq OWNER TO postgres;

--
-- Name: templates_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.templates_id_seq OWNED BY public.templates.id;


--
-- Name: test_table; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.test_table (
    "Id" bigint NOT NULL,
    name "char",
    age bigint
);


ALTER TABLE public.test_table OWNER TO postgres;

--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    id integer NOT NULL,
    username character varying(50) NOT NULL,
    name character varying(50) NOT NULL,
    surname character varying(50) NOT NULL,
    password character varying(255) NOT NULL,
    is_admin boolean
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: websites_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.websites_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.websites_id_seq OWNER TO postgres;

--
-- Name: websites_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.websites_id_seq OWNED BY public.events.id;


--
-- Name: events id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.events ALTER COLUMN id SET DEFAULT nextval('public.websites_id_seq'::regclass);


--
-- Name: invitation id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.invitation ALTER COLUMN id SET DEFAULT nextval('public.new_table_id_seq'::regclass);


--
-- Name: templates id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.templates ALTER COLUMN id SET DEFAULT nextval('public.templates_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: invitation; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: templates; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.templates (id, displayname, viewname, type, created_at, updated_at) VALUES (1, 'Birthday Template 1', 'birthday_template_1.html', 'birthday', '2024-09-18 02:41:30.595756', '2024-09-18 02:41:30.595756');


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.users (id, username, name, surname, password, is_admin) VALUES (1, 'janedoe', 'Jane', 'Doe', 'newsecretpassword', false);
INSERT INTO public.users (id, username, name, surname, password, is_admin) VALUES (4, 'admin', 'Petr', 'Poghosyan', 'supersecret', true);
INSERT INTO public.users (id, username, name, surname, password, is_admin) VALUES (11, 'ivanivanov', 'Ivan', 'Ivanov', 'Password1)', false);


--
-- Name: new_table_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.new_table_id_seq', 1, false);


--
-- Name: templates_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.templates_id_seq', 2, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.users_id_seq', 15, true);


--
-- Name: websites_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.websites_id_seq', 26, true);


--
-- Name: invitation new_table_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.invitation
    ADD CONSTRAINT new_table_pkey PRIMARY KEY (id);


--
-- Name: templates templates_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.templates
    ADD CONSTRAINT templates_pkey PRIMARY KEY (id);


--
-- Name: test_table test_table_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.test_table
    ADD CONSTRAINT test_table_pkey PRIMARY KEY ("Id");


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- Name: events websites_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.events
    ADD CONSTRAINT websites_pkey PRIMARY KEY (id);


--
-- Name: events websites_template_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.events
    ADD CONSTRAINT websites_template_id_fkey FOREIGN KEY (template_id) REFERENCES public.templates(id);


--
-- PostgreSQL database dump complete
--

