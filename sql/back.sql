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
-- Data for Name: events; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.events (id, internal_name, template_id, user_id, date, address_country, address_city, address_line, display_name, hall_name, unique_domain, is_deleted) VALUES (2, 'example_internal_name', 1, 1001, '2024-09-03 00:00:00', 'Armenia', 'Erevan', '123 Main St.', 'Example Site', 'Main Hall', 'example.com', false);
INSERT INTO public.events (id, internal_name, template_id, user_id, date, address_country, address_city, address_line, display_name, hall_name, unique_domain, is_deleted) VALUES (4, 'example_internal_name2', 1, 1001, '2024-09-03 12:34:59', 'Armenia', 'Erevan', '123 Main St.', 'Example Site2', 'Main Hall', 'example.com2', false);
INSERT INTO public.events (id, internal_name, template_id, user_id, date, address_country, address_city, address_line, display_name, hall_name, unique_domain, is_deleted) VALUES (7, 'example_internal_name3', 1, 1001, '2021-11-16 11:24:13', 'Armenia', 'Erevan', '123 Main St.', 'Example Site2', 'Main Hall', 'example.com3', false);
INSERT INTO public.events (id, internal_name, template_id, user_id, date, address_country, address_city, address_line, display_name, hall_name, unique_domain, is_deleted) VALUES (8, 'example_internal_name4', 1, 1001, '2021-11-16 11:24:13', 'Armenia', 'Erevan', '123 Main St.', 'Example Site2', 'Main Hall', 'example.com4', false);
INSERT INTO public.events (id, internal_name, template_id, user_id, date, address_country, address_city, address_line, display_name, hall_name, unique_domain, is_deleted) VALUES (9, 'test', 2, 11, '2024-09-14 02:59:00', 'test', 'test', 'tests', 'test', 'test', 'test', false);
INSERT INTO public.events (id, internal_name, template_id, user_id, date, address_country, address_city, address_line, display_name, hall_name, unique_domain, is_deleted) VALUES (22, 'a', 1, 11, '2024-09-17 18:07:00', 'a', 'a', 'a', 'a', 'a', 'a', false);
INSERT INTO public.events (id, internal_name, template_id, user_id, date, address_country, address_city, address_line, display_name, hall_name, unique_domain, is_deleted) VALUES (25, 'w', 1, 11, '2024-09-17 18:11:00', 'w', 'w', 'w', 'w', 'w', 'ww', true);
INSERT INTO public.events (id, internal_name, template_id, user_id, date, address_country, address_city, address_line, display_name, hall_name, unique_domain, is_deleted) VALUES (24, 'w', 1, 11, '2024-09-17 18:11:00', 'w', 'w', 'w', 'w', 'w', 'w', true);
INSERT INTO public.events (id, internal_name, template_id, user_id, date, address_country, address_city, address_line, display_name, hall_name, unique_domain, is_deleted) VALUES (23, 'f', 1, 11, '2024-09-17 18:09:00', 'f', 'f', 'f', 'f', 'f', 'f', true);
INSERT INTO public.events (id, internal_name, template_id, user_id, date, address_country, address_city, address_line, display_name, hall_name, unique_domain, is_deleted) VALUES (26, 'er', 3, 11, '2024-09-18 20:47:00', 'er', 'er', 'er', 'er', 'er', 'er', false);
INSERT INTO public.events (id, internal_name, template_id, user_id, date, address_country, address_city, address_line, display_name, hall_name, unique_domain, is_deleted) VALUES (14, 'test33', 1, 11, '2024-09-16 19:47:00', 'test3', 'test3', 'test3', 'test3', 'test3', 'test3', false);


--
-- Data for Name: invitation; Type: TABLE DATA; Schema: public; Owner: postgres
--



--
-- Data for Name: templates; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.templates (id, displayname, viewname, type, created_at, updated_at) VALUES (1, 'Updated Template', 'SampleView2', 'TypeA', '2024-09-02 07:03:59.669016', '2024-09-02 07:03:59.676657');
INSERT INTO public.templates (id, displayname, viewname, type, created_at, updated_at) VALUES (2, 'Update_template2', 'Samplevew3', 'TypeB', '2024-09-06 05:49:20.211591', '2024-09-06 05:49:20.211591');
INSERT INTO public.templates (id, displayname, viewname, type, created_at, updated_at) VALUES (3, 'Birthday Template 1', 'birthday_template_1.html', 'birthday', '2024-09-18 02:41:30.595756', '2024-09-18 02:41:30.595756');


--
-- Data for Name: test_table; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.test_table ("Id", name, age) VALUES (1, 'T', 18);
INSERT INTO public.test_table ("Id", name, age) VALUES (2, 'A', 20);
INSERT INTO public.test_table ("Id", name, age) VALUES (3, 'C', 20);


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

