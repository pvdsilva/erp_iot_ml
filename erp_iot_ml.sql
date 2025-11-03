-- phpMyAdmin SQL Dump
-- version 5.2.1deb3
-- https://www.phpmyadmin.net/
--
-- Host: localhost:3306
-- Tempo de geração: 02/11/2025 às 23:42
-- Versão do servidor: 10.11.13-MariaDB-0ubuntu0.24.04.1
-- Versão do PHP: 8.3.6

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Banco de dados: `erp_iot_ml`
--

-- --------------------------------------------------------

--
-- Estrutura para tabela `clientes`
--

CREATE TABLE `clientes` (
  `id` int(11) NOT NULL,
  `tipo` enum('pf','pj','padrao') NOT NULL DEFAULT 'pf',
  `nome` varchar(100) NOT NULL,
  `documento` varchar(18) DEFAULT NULL,
  `data_nascimento` date DEFAULT NULL,
  `religiao` varchar(50) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `telefone_fixo` varchar(15) DEFAULT NULL,
  `telefone_celular` varchar(15) DEFAULT NULL,
  `endereco` text DEFAULT NULL,
  `ativo` tinyint(1) DEFAULT 1,
  `data_criacao` timestamp NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Despejando dados para a tabela `clientes`
--

INSERT INTO `clientes` (`id`, `tipo`, `nome`, `documento`, `data_nascimento`, `religiao`, `email`, `telefone_fixo`, `telefone_celular`, `endereco`, `ativo`, `data_criacao`) VALUES
(1, 'padrao', 'Teste cliente 1', '00000000000', '1991-07-20', 'Cristão', 'testecliente1@test.com.br', '', '(13) 000000000', 'Cidade Test1', 1, '2025-09-28 01:51:16');

-- --------------------------------------------------------

--
-- Estrutura para tabela `empresa`
--

CREATE TABLE `empresa` (
  `id` int(11) NOT NULL,
  `tipo` enum('pf','pj') NOT NULL,
  `nome` varchar(100) NOT NULL,
  `documento` varchar(18) NOT NULL,
  `email` varchar(100) DEFAULT NULL,
  `telefone` varchar(15) DEFAULT NULL,
  `endereco` text DEFAULT NULL,
  `data_criacao` timestamp NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Despejando dados para a tabela `empresa`
--

INSERT INTO `empresa` (`id`, `tipo`, `nome`, `documento`, `email`, `telefone`, `endereco`, `data_criacao`) VALUES
(1, 'pf', 'Chaveiro Test', '00.000.000/0000-00', 'chaveiro@test.com.br', '(13) 0000-0000', 'Rua José Quirino Dantas, 231 - Jd. Nova República - Cubatão- SP - Cidade - SP.', '2025-09-17 19:32:47');

-- --------------------------------------------------------

--
-- Estrutura para tabela `entradas_estoque`
--

CREATE TABLE `entradas_estoque` (
  `id` int(11) NOT NULL,
  `produto_id` int(11) NOT NULL,
  `quantidade` decimal(10,2) NOT NULL,
  `data_entrada` date NOT NULL,
  `nota_fiscal` varchar(50) DEFAULT NULL,
  `fornecedor_id` int(11) DEFAULT NULL,
  `observacoes` text DEFAULT NULL,
  `usuario_id` int(11) DEFAULT NULL,
  `data_criacao` timestamp NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estrutura para tabela `financeiro`
--

CREATE TABLE `financeiro` (
  `id` int(11) NOT NULL,
  `tipo` enum('receita','despesa') NOT NULL,
  `categoria` varchar(50) DEFAULT NULL,
  `descricao` text DEFAULT NULL,
  `valor` decimal(10,2) NOT NULL,
  `data_lancamento` date NOT NULL,
  `forma_pagamento` varchar(30) DEFAULT NULL,
  `usuario_id` int(11) DEFAULT NULL,
  `data_criacao` timestamp NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estrutura para tabela `fornecedores`
--

CREATE TABLE `fornecedores` (
  `id` int(11) NOT NULL,
  `tipo` enum('pf','pj') NOT NULL,
  `nome` varchar(100) NOT NULL,
  `documento` varchar(18) NOT NULL,
  `email` varchar(100) DEFAULT NULL,
  `telefone` varchar(15) DEFAULT NULL,
  `endereco` text DEFAULT NULL,
  `ativo` tinyint(1) DEFAULT 1,
  `data_criacao` timestamp NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Despejando dados para a tabela `fornecedores`
--

INSERT INTO `fornecedores` (`id`, `tipo`, `nome`, `documento`, `email`, `telefone`, `endereco`, `ativo`, `data_criacao`) VALUES
(1, 'pj', 'Fornecedor  Test 1', '00.000.000/0000-00', 'fornecedortest1@test.com.br', '(13) 0000-0000', 'Cidade Test 1', 1, '2025-09-28 01:23:45'),
(3, 'pj', 'Fornecedor Test 2', '00.000.000/0000-02', 'fornecedortest2@test.com.br', '(13) 0000-0002', 'Cidade Test2', 1, '2025-09-28 01:27:10');

-- --------------------------------------------------------

--
-- Estrutura para tabela `itens_orcamento`
--

CREATE TABLE `itens_orcamento` (
  `id` int(11) NOT NULL,
  `id_orcamento` int(11) NOT NULL,
  `id_produto` int(11) NOT NULL,
  `quantidade` decimal(10,2) NOT NULL,
  `preco_unitario` decimal(10,2) NOT NULL,
  `total_item` decimal(10,2) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Despejando dados para a tabela `itens_orcamento`
--

INSERT INTO `itens_orcamento` (`id`, `id_orcamento`, `id_produto`, `quantidade`, `preco_unitario`, `total_item`) VALUES
(1, 3, 3, 2.00, 30.00, 60.00),
(2, 3, 11, 1.00, 19.50, 19.50),
(3, 4, 12, 19.00, 22.50, 427.50);

-- --------------------------------------------------------

--
-- Estrutura para tabela `itens_venda`
--

CREATE TABLE `itens_venda` (
  `id` int(11) NOT NULL,
  `id_venda` int(11) NOT NULL,
  `id_produto` int(11) NOT NULL,
  `quantidade` decimal(10,2) NOT NULL,
  `preco_unitario` decimal(10,2) NOT NULL,
  `total_item` decimal(10,2) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Despejando dados para a tabela `itens_venda`
--

INSERT INTO `itens_venda` (`id`, `id_venda`, `id_produto`, `quantidade`, `preco_unitario`, `total_item`) VALUES
(5, 15, 6, 2.00, 30.00, 60.00),
(6, 16, 9, 20.00, 296.25, 5925.00),
(7, 17, 10, 1.00, 22.50, 22.50),
(8, 18, 1, 1.00, 15.00, 15.00),
(9, 19, 3, 1.00, 30.00, 30.00),
(10, 20, 8, 1.00, 150.00, 150.00),
(11, 21, 6, 1.00, 30.00, 30.00),
(12, 22, 8, 1.00, 150.00, 150.00),
(13, 23, 12, 1.00, 22.50, 22.50),
(14, 24, 1, 2.00, 15.00, 30.00),
(15, 25, 11, 1.00, 19.50, 19.50),
(16, 26, 2, 2.00, 22.50, 45.00),
(17, 27, 11, 1.00, 19.50, 19.50),
(18, 28, 9, 10.00, 296.25, 2962.50),
(19, 29, 10, 1.00, 22.50, 22.50),
(20, 30, 10, 10.00, 22.50, 225.00),
(21, 31, 8, 1.00, 150.00, 150.00),
(22, 32, 8, 1.00, 150.00, 150.00),
(23, 33, 8, 1.00, 150.00, 150.00),
(26, 37, 3, 2.00, 30.00, 60.00),
(27, 37, 11, 1.00, 19.50, 19.50),
(28, 38, 13, 1.00, 15.00, 15.00),
(29, 39, 8, 1.00, 150.00, 150.00),
(30, 39, 6, 1.00, 30.00, 30.00),
(31, 40, 5, 1.00, 21.00, 21.00),
(32, 41, 5, 1.00, 21.00, 21.00),
(33, 42, 6, 1.00, 30.00, 30.00),
(34, 43, 5, 48.00, 21.00, 1008.00),
(35, 44, 4, 1.00, 15.00, 15.00),
(36, 45, 7, 5.00, 75.00, 375.00),
(37, 46, 8, 1.00, 150.00, 150.00),
(38, 47, 5, 1.00, 21.00, 21.00),
(39, 47, 8, 23.00, 150.00, 3450.00),
(40, 48, 12, 1.00, 22.50, 22.50),
(41, 49, 4, 1.00, 15.00, 15.00),
(42, 50, 5, 1.00, 21.00, 21.00),
(43, 51, 8, 10.00, 150.00, 1500.00),
(44, 52, 4, 20.00, 15.00, 300.00),
(45, 53, 7, 1.00, 75.00, 75.00),
(46, 54, 7, 20.00, 75.00, 1500.00),
(47, 55, 7, 1.00, 75.00, 75.00),
(48, 56, 7, 73.00, 75.00, 5475.00),
(49, 57, 5, 43.00, 21.00, 903.00),
(50, 58, 7, 1.00, 75.00, 75.00),
(51, 59, 6, 1.00, 30.00, 30.00),
(52, 60, 13, 3.00, 15.00, 45.00),
(53, 61, 12, 1.00, 22.50, 22.50),
(54, 62, 8, 1.00, 150.00, 150.00),
(55, 63, 7, 1.00, 75.00, 75.00),
(56, 64, 4, 1.00, 15.00, 15.00),
(57, 65, 7, 1.00, 75.00, 75.00),
(58, 66, 7, 13.00, 75.00, 975.00),
(59, 67, 4, 1.00, 15.00, 15.00),
(60, 68, 7, 1.00, 75.00, 75.00),
(61, 69, 7, 1.00, 75.00, 75.00),
(62, 70, 4, 20.00, 15.00, 300.00),
(63, 71, 13, 1.00, 15.00, 15.00),
(64, 72, 6, 1.00, 30.00, 30.00),
(65, 73, 4, 1.00, 15.00, 15.00),
(66, 73, 12, 1.00, 22.50, 22.50),
(67, 74, 10, 60.00, 22.50, 1350.00),
(68, 75, 7, 1.00, 75.00, 75.00),
(69, 76, 7, 30.00, 75.00, 2250.00),
(70, 77, 11, 30.00, 19.50, 585.00),
(71, 78, 8, 25.00, 150.00, 3750.00),
(72, 79, 7, 1.00, 75.00, 75.00),
(73, 80, 7, 1.00, 75.00, 75.00),
(74, 81, 4, 1.00, 15.00, 15.00),
(75, 81, 14, 1.00, 30.00, 30.00),
(76, 82, 11, 1.00, 19.50, 19.50),
(77, 83, 7, 1.00, 75.00, 75.00),
(78, 84, 13, 1.00, 15.00, 15.00),
(79, 85, 4, 24.00, 15.00, 360.00),
(80, 86, 7, 1.00, 75.00, 75.00),
(81, 87, 10, 1.00, 22.50, 22.50),
(82, 88, 16, 2.00, 15.00, 30.00),
(83, 88, 5, 1.00, 21.00, 21.00),
(84, 89, 8, 1.00, 150.00, 150.00);

-- --------------------------------------------------------

--
-- Estrutura para tabela `movimentacoes_estoque`
--

CREATE TABLE `movimentacoes_estoque` (
  `id` int(11) NOT NULL,
  `produto_id` int(11) NOT NULL,
  `tipo` enum('entrada','saida') NOT NULL,
  `quantidade` decimal(10,2) NOT NULL,
  `origem` varchar(50) DEFAULT NULL,
  `referencia_id` int(11) DEFAULT NULL,
  `usuario_id` int(11) DEFAULT NULL,
  `data_movimentacao` timestamp NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estrutura para tabela `orcamentos`
--

CREATE TABLE `orcamentos` (
  `id` int(11) NOT NULL,
  `id_cliente` int(11) DEFAULT NULL,
  `data_criacao` timestamp NULL DEFAULT current_timestamp(),
  `forma_pagamento` enum('dinheiro','cartao_credito','cartao_debito','pix','transferencia') NOT NULL,
  `validade` int(11) DEFAULT 7,
  `condicoes_pagamento` text DEFAULT NULL,
  `observacoes` text DEFAULT NULL,
  `valor_total` decimal(10,2) NOT NULL,
  `status` enum('pendente','aprovado','cancelado','convertido') NOT NULL DEFAULT 'pendente',
  `desconto` decimal(10,2) DEFAULT 0.00
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Despejando dados para a tabela `orcamentos`
--

INSERT INTO `orcamentos` (`id`, `id_cliente`, `data_criacao`, `forma_pagamento`, `validade`, `condicoes_pagamento`, `observacoes`, `valor_total`, `status`, `desconto`) VALUES
(1, 1, '2025-10-03 01:51:06', 'cartao_credito', 7, '', '', 0.00, 'cancelado', 0.00),
(2, 1, '2025-10-26 01:42:29', 'cartao_credito', 7, '', 'test', 0.00, 'cancelado', 0.00),
(3, 1, '2025-10-26 02:15:53', 'cartao_credito', 7, '', '', 79.50, 'convertido', 0.00),
(4, 1, '2025-10-27 18:58:49', 'dinheiro', 7, '', '', 427.50, 'pendente', 0.00);

-- --------------------------------------------------------

--
-- Estrutura para tabela `produtos`
--

CREATE TABLE `produtos` (
  `id` int(11) NOT NULL,
  `nome` varchar(100) NOT NULL,
  `data_entrada` date NOT NULL,
  `quantidade` decimal(10,2) NOT NULL,
  `unidade` enum('un','kg','g','l','ml','m','cm','cx','pc') NOT NULL,
  `id_fornecedor` int(11) DEFAULT NULL,
  `descricao` text DEFAULT NULL,
  `nota_fiscal` varchar(50) DEFAULT NULL,
  `preco_custo` decimal(10,2) NOT NULL,
  `margem_lucro` decimal(5,2) NOT NULL,
  `preco_venda` decimal(10,2) NOT NULL,
  `estoque_minimo` int(11) DEFAULT 0,
  `ativo` tinyint(1) DEFAULT 1,
  `data_criacao` timestamp NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Despejando dados para a tabela `produtos`
--

INSERT INTO `produtos` (`id`, `nome`, `data_entrada`, `quantidade`, `unidade`, `id_fornecedor`, `descricao`, `nota_fiscal`, `preco_custo`, `margem_lucro`, `preco_venda`, `estoque_minimo`, `ativo`, `data_criacao`) VALUES
(1, 'chave 1', '2024-09-27', 0.00, 'un', 1, 'chave 1', '00001', 10.00, 50.00, 15.00, 5, 1, '2025-09-28 01:28:58'),
(2, 'chave 2', '2025-09-27', 0.00, 'un', 3, 'chave 2', '0002', 15.00, 50.00, 22.50, 5, 1, '2025-09-28 01:30:02'),
(3, 'chave 4', '2025-09-27', 0.00, 'un', 1, 'chave 4', '0002', 20.00, 50.00, 30.00, 5, 1, '2025-09-28 01:31:11'),
(4, 'chave 4', '2025-09-27', 30.00, 'un', 3, 'chave 4', '00001', 10.00, 50.00, 15.00, 5, 1, '2025-09-28 01:35:39'),
(5, 'chave 5', '2025-09-27', 4.00, 'un', 1, 'chave 5', '0001', 14.00, 50.00, 21.00, 5, 1, '2025-09-28 01:36:48'),
(6, 'chave 7', '2025-09-27', 43.00, 'un', 3, 'chave 7', '0003', 20.00, 50.00, 30.00, 5, 1, '2025-09-28 01:37:58'),
(7, 'chave 6', '2025-09-27', 47.00, 'un', 3, 'chave 6', '0004', 50.00, 50.00, 75.00, 5, 1, '2025-09-28 01:40:47'),
(8, 'chave 8', '2025-09-27', 4.00, 'un', 1, 'chave 8', '0003', 100.00, 50.00, 150.00, 5, 1, '2025-09-28 01:41:46'),
(9, 'chave 9', '2025-09-27', 0.00, 'un', 3, 'chave 9', '0004', 197.50, 50.00, 296.25, 5, 1, '2025-09-28 01:43:44'),
(10, 'chave 10', '2025-09-27', 12.00, 'un', 1, 'chave 10', '0004', 15.00, 50.00, 22.50, 5, 1, '2025-09-28 01:45:13'),
(11, 'chave 11', '2025-09-27', 26.00, 'un', 1, 'chave 11', '0003', 13.00, 50.00, 19.50, 5, 1, '2025-09-28 01:47:35'),
(12, 'chave 12', '2025-10-25', 16.00, 'un', 3, '', '0005', 15.00, 50.00, 22.50, 3, 1, '2025-10-26 00:42:21'),
(13, 'chave 1', '2025-10-26', 14.00, 'un', 1, '', '', 10.00, 50.00, 15.00, 5, 1, '2025-10-27 00:23:15'),
(14, 'chave 2', '2025-10-28', 29.00, 'un', 1, '', '0004', 20.00, 50.00, 30.00, 0, 1, '2025-10-28 17:25:47'),
(15, 'chave 9', '2025-10-28', 20.00, 'un', 3, '', '0004', 10.00, 50.00, 15.00, 5, 1, '2025-10-28 21:57:58'),
(16, 'chave 13', '2025-11-01', 28.00, 'un', 1, '', '0004', 10.00, 50.00, 15.00, 5, 1, '2025-11-02 00:11:29');

-- --------------------------------------------------------

--
-- Estrutura para tabela `usuarios`
--

CREATE TABLE `usuarios` (
  `id` int(11) NOT NULL,
  `username` varchar(50) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `tipo` enum('funcionario','administrador','proprietario') NOT NULL,
  `nome` varchar(100) NOT NULL,
  `cpf` varchar(14) DEFAULT NULL,
  `telefone` varchar(15) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `endereco` text DEFAULT NULL,
  `tipo_sanguineo` varchar(3) DEFAULT NULL,
  `cor` varchar(20) DEFAULT NULL,
  `altura` decimal(3,2) DEFAULT NULL,
  `cor_cabelos` varchar(20) DEFAULT NULL,
  `foto` varchar(255) DEFAULT NULL,
  `estado_civil` varchar(20) DEFAULT NULL,
  `conjugue` varchar(100) DEFAULT NULL,
  `filhos` int(11) DEFAULT NULL,
  `funcao` varchar(50) DEFAULT NULL,
  `departamento` varchar(50) DEFAULT NULL,
  `ativo` tinyint(1) DEFAULT 1,
  `data_criacao` timestamp NULL DEFAULT current_timestamp(),
  `dashboard_layout` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Despejando dados para a tabela `usuarios`
--

INSERT INTO `usuarios` (`id`, `username`, `password_hash`, `tipo`, `nome`, `cpf`, `telefone`, `email`, `endereco`, `tipo_sanguineo`, `cor`, `altura`, `cor_cabelos`, `foto`, `estado_civil`, `conjugue`, `filhos`, `funcao`, `departamento`, `ativo`, `data_criacao`, `dashboard_layout`) VALUES
(1, 'Admin', '95d8559aac1ef7602f7e9282db7e1ec624b2fe17731368c644e3161c6bf5c633', 'proprietario', 'Administrador', '000.000.000-00', NULL, 'admin@empresa.com', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0, 'Proprietário', 'Administração', 1, '2025-09-17 19:32:47', NULL),
(2, 'Master', '397270b934080c5cf1b21a930bc22dfae5195e390485c040e55bf674523d0e4a', 'administrador', 'Master ', '00000000000', '(13) 00000-0000', 'mastertest@test.com.br', 'Cidade Test 2', NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0, 'Administrador Master', 'Gestão', 1, '2025-09-28 01:59:02', NULL);

-- --------------------------------------------------------

--
-- Estrutura para tabela `vendas`
--

CREATE TABLE `vendas` (
  `id` int(11) NOT NULL,
  `id_cliente` int(11) DEFAULT NULL,
  `data_venda` timestamp NULL DEFAULT current_timestamp(),
  `forma_pagamento` varchar(50) NOT NULL,
  `observacoes` text DEFAULT NULL,
  `desconto` decimal(10,2) DEFAULT 0.00,
  `valor_total` decimal(10,2) NOT NULL,
  `status` enum('pendente','concluida','cancelada') DEFAULT 'concluida'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Despejando dados para a tabela `vendas`
--

INSERT INTO `vendas` (`id`, `id_cliente`, `data_venda`, `forma_pagamento`, `observacoes`, `desconto`, `valor_total`, `status`) VALUES
(1, 1, '2025-10-03 01:50:14', 'cartao_credito', '', 0.00, 0.00, 'concluida'),
(2, NULL, '2025-10-08 00:55:20', 'cartao_credito', '', 0.00, 0.00, 'concluida'),
(3, 1, '2025-10-15 02:30:31', 'cartao_debito', '', 0.00, 0.00, 'concluida'),
(4, 1, '2025-10-20 00:58:56', 'dinheiro', '', 0.00, 0.00, 'concluida'),
(5, 1, '2025-10-20 00:59:28', 'cartao_debito', '', 0.00, 0.00, 'concluida'),
(6, 1, '2025-10-20 01:00:09', 'pix', '', 0.00, 0.00, 'concluida'),
(7, 1, '2025-10-23 03:25:30', 'transferencia', '', 0.00, 0.00, 'concluida'),
(8, 1, '2025-10-23 03:27:25', 'cartao_debito', '', 0.00, 0.00, 'concluida'),
(9, 1, '2025-10-24 22:39:28', 'transferencia', '', 0.00, 0.00, 'concluida'),
(10, 1, '2025-10-24 23:15:13', 'cartao_debito', '', 0.00, 0.00, 'concluida'),
(13, 1, '2025-10-25 01:56:37', 'cartao_credito', '', 0.00, 0.00, 'concluida'),
(14, 1, '2025-10-25 22:07:38', 'dinheiro', '', 0.00, 0.00, 'concluida'),
(15, 1, '2025-10-25 22:53:44', 'dinheiro', '', 0.00, 60.00, 'concluida'),
(16, 1, '2025-10-25 22:54:40', 'pix', '', 0.00, 5925.00, 'concluida'),
(17, 1, '2025-10-25 23:13:15', 'transferencia', '', 0.00, 22.50, 'concluida'),
(18, 1, '2025-10-25 23:14:44', 'dinheiro', '', 0.00, 15.00, 'concluida'),
(19, 1, '2025-10-25 23:30:36', 'dinheiro', '', 0.00, 30.00, 'concluida'),
(20, 1, '2025-10-25 23:36:51', 'dinheiro', '', 0.00, 150.00, 'concluida'),
(21, 1, '2025-10-26 00:07:53', 'pix', '', 0.00, 30.00, 'concluida'),
(22, 1, '2025-10-26 00:19:02', 'dinheiro', '', 0.00, 150.00, 'concluida'),
(23, 1, '2025-10-26 00:45:36', 'dinheiro', '', 0.00, 22.50, 'concluida'),
(24, 1, '2025-10-26 01:11:34', 'dinheiro', '', 0.00, 30.00, 'concluida'),
(25, 1, '2025-10-26 01:31:06', 'pix', '', 0.00, 19.50, 'concluida'),
(26, 1, '2025-10-26 01:32:19', 'dinheiro', '', 0.00, 45.00, 'concluida'),
(27, 1, '2025-10-26 17:19:13', 'pix', '', 0.00, 19.50, 'concluida'),
(28, 1, '2025-10-26 19:59:48', 'pix', '', 0.00, 2962.50, 'concluida'),
(29, 1, '2025-10-26 20:01:11', 'dinheiro', '', 0.00, 22.50, 'concluida'),
(30, 1, '2025-10-26 20:03:17', 'dinheiro', '', 0.00, 225.00, 'concluida'),
(31, 1, '2025-10-26 20:10:02', 'transferencia', '', 0.00, 150.00, 'concluida'),
(32, 1, '2025-10-26 20:35:48', 'transferencia', '', 0.00, 150.00, 'concluida'),
(33, 1, '2025-10-26 21:17:23', 'transferencia', '', 0.00, 150.00, 'cancelada'),
(37, 1, '2025-10-27 00:17:30', 'cartao_credito', 'Convertido do orçamento #3', 0.00, 79.50, 'concluida'),
(38, 1, '2025-10-27 14:48:02', 'pix', '', 0.00, 15.00, 'concluida'),
(39, 1, '2025-10-27 15:14:19', 'pix', '', 0.00, 180.00, 'concluida'),
(40, 1, '2025-10-27 15:18:02', 'transferencia', '', 0.00, 21.00, 'concluida'),
(41, 1, '2025-10-27 15:18:58', 'transferencia', '', 0.00, 21.00, 'concluida'),
(42, 1, '2025-10-27 15:55:01', 'dinheiro', '', 0.00, 30.00, 'concluida'),
(43, 1, '2025-10-27 17:40:40', 'pix', '', 0.00, 1008.00, 'concluida'),
(44, 1, '2025-10-27 17:42:10', 'transferencia', '', 0.00, 15.00, 'concluida'),
(45, 1, '2025-10-27 17:43:04', 'transferencia', '', 0.00, 375.00, 'concluida'),
(46, 1, '2025-10-27 18:57:19', 'pix', '', 0.00, 150.00, 'concluida'),
(47, 1, '2025-10-28 14:03:42', 'transferencia', '', 0.00, 3471.00, 'concluida'),
(48, 1, '2025-10-28 14:04:03', 'dinheiro', '', 0.00, 22.50, 'concluida'),
(49, 1, '2025-10-28 14:05:00', 'dinheiro', '', 0.00, 15.00, 'concluida'),
(50, 1, '2025-10-28 15:27:19', 'dinheiro', '', 0.00, 21.00, 'concluida'),
(51, 1, '2025-10-28 15:27:46', 'dinheiro', '', 0.00, 1500.00, 'concluida'),
(52, 1, '2025-10-28 17:21:06', 'dinheiro', '', 0.00, 300.00, 'concluida'),
(53, 1, '2025-10-28 17:21:34', 'pix', '', 0.00, 75.00, 'concluida'),
(54, 1, '2025-10-28 17:22:51', 'transferencia', '', 0.00, 1500.00, 'concluida'),
(55, 1, '2025-10-28 23:29:18', 'transferencia', '', 0.00, 75.00, 'concluida'),
(56, 1, '2025-10-28 23:55:47', 'pix', '', 0.00, 5475.00, 'concluida'),
(57, 1, '2025-10-29 00:10:25', 'pix', '', 0.00, 903.00, 'concluida'),
(58, 1, '2025-10-29 02:42:02', 'pix', '', 0.00, 75.00, 'concluida'),
(59, 1, '2025-10-30 01:47:32', 'pix', '', 0.00, 30.00, 'concluida'),
(60, 1, '2025-10-30 01:48:14', 'dinheiro', '', 0.00, 45.00, 'concluida'),
(61, 1, '2025-10-30 01:59:01', 'dinheiro', '', 0.00, 22.50, 'concluida'),
(62, 1, '2025-10-30 02:39:08', 'transferencia', '', 0.00, 150.00, 'concluida'),
(63, 1, '2025-10-30 02:39:39', 'pix', '', 0.00, 75.00, 'concluida'),
(64, 1, '2025-10-30 03:04:48', 'Cartão de Débito', '', 0.00, 15.00, 'concluida'),
(65, 1, '2025-10-30 03:06:44', 'Cartão de Crédito', '', 0.00, 75.00, 'concluida'),
(66, 1, '2025-10-31 02:15:10', 'Dinheiro', '', 0.00, 975.00, 'concluida'),
(67, 1, '2025-10-31 02:15:37', 'Cartão de Crédito', '', 0.00, 15.00, 'concluida'),
(68, 1, '2025-10-31 02:20:33', 'Transferência', '', 0.00, 75.00, 'concluida'),
(69, 1, '2025-11-01 00:59:36', 'Dinheiro', '', 0.00, 75.00, 'concluida'),
(70, 1, '2025-11-01 01:00:53', 'Transferência', '', 0.00, 300.00, 'concluida'),
(71, 1, '2025-11-01 01:02:18', 'Cartão de Crédito', '', 0.00, 15.00, 'concluida'),
(72, 1, '2025-11-01 01:02:35', 'Cartão de Débito', '', 0.00, 30.00, 'concluida'),
(73, 1, '2025-11-01 01:03:15', 'Dinheiro', '', 0.00, 37.50, 'concluida'),
(74, 1, '2025-11-01 01:07:42', 'Cartão de Crédito', '', 0.00, 1350.00, 'concluida'),
(75, 1, '2025-11-01 01:46:44', 'Cartão de Débito', '', 0.00, 75.00, 'concluida'),
(76, 1, '2025-11-01 02:24:57', 'Cartão de Crédito', '', 0.00, 2250.00, 'concluida'),
(77, 1, '2025-11-01 02:26:14', 'PIX', '', 0.00, 585.00, 'concluida'),
(78, 1, '2025-11-01 02:27:24', 'Cartão de Crédito', '', 0.00, 3750.00, 'concluida'),
(79, 1, '2025-11-01 03:35:35', 'Transferência', '', 0.00, 75.00, 'concluida'),
(80, 1, '2025-11-01 12:40:10', 'Transferência', '', 0.00, 75.00, 'concluida'),
(81, 1, '2025-11-01 12:41:27', 'PIX', '', 0.00, 45.00, 'concluida'),
(82, 1, '2025-11-01 14:29:25', 'Dinheiro', '', 0.00, 19.50, 'concluida'),
(83, 1, '2025-11-01 15:18:01', 'Cartão de Débito', '', 0.00, 75.00, 'concluida'),
(84, 1, '2025-11-01 16:38:45', 'Cartão de Crédito', '', 0.00, 15.00, 'concluida'),
(85, 1, '2025-11-01 17:23:50', 'Cartão de Crédito', '', 0.00, 360.00, 'concluida'),
(86, 1, '2025-11-01 20:57:21', 'Transferência', '', 0.00, 75.00, 'concluida'),
(87, 1, '2025-11-01 21:46:36', 'PIX', '', 0.00, 22.50, 'concluida'),
(88, 1, '2025-11-02 00:16:38', 'Cartão de Débito', '', 0.00, 51.00, 'concluida'),
(89, 1, '2025-11-02 02:36:12', 'Dinheiro', '', 0.00, 150.00, 'concluida');

-- --------------------------------------------------------

--
-- Estrutura para tabela `venda_itens`
--

CREATE TABLE `venda_itens` (
  `id` int(11) NOT NULL,
  `venda_id` int(11) NOT NULL,
  `produto_id` int(11) NOT NULL,
  `quantidade` decimal(10,2) NOT NULL,
  `preco_unitario` decimal(10,2) NOT NULL,
  `subtotal` decimal(10,2) NOT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Índices para tabelas despejadas
--

--
-- Índices de tabela `clientes`
--
ALTER TABLE `clientes`
  ADD PRIMARY KEY (`id`);

--
-- Índices de tabela `empresa`
--
ALTER TABLE `empresa`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `documento` (`documento`);

--
-- Índices de tabela `entradas_estoque`
--
ALTER TABLE `entradas_estoque`
  ADD PRIMARY KEY (`id`),
  ADD KEY `produto_id` (`produto_id`),
  ADD KEY `fornecedor_id` (`fornecedor_id`),
  ADD KEY `usuario_id` (`usuario_id`);

--
-- Índices de tabela `financeiro`
--
ALTER TABLE `financeiro`
  ADD PRIMARY KEY (`id`),
  ADD KEY `usuario_id` (`usuario_id`);

--
-- Índices de tabela `fornecedores`
--
ALTER TABLE `fornecedores`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `documento` (`documento`);

--
-- Índices de tabela `itens_orcamento`
--
ALTER TABLE `itens_orcamento`
  ADD PRIMARY KEY (`id`),
  ADD KEY `id_orcamento` (`id_orcamento`),
  ADD KEY `id_produto` (`id_produto`);

--
-- Índices de tabela `itens_venda`
--
ALTER TABLE `itens_venda`
  ADD PRIMARY KEY (`id`),
  ADD KEY `id_venda` (`id_venda`),
  ADD KEY `id_produto` (`id_produto`);

--
-- Índices de tabela `movimentacoes_estoque`
--
ALTER TABLE `movimentacoes_estoque`
  ADD PRIMARY KEY (`id`),
  ADD KEY `produto_id` (`produto_id`),
  ADD KEY `usuario_id` (`usuario_id`);

--
-- Índices de tabela `orcamentos`
--
ALTER TABLE `orcamentos`
  ADD PRIMARY KEY (`id`),
  ADD KEY `id_cliente` (`id_cliente`);

--
-- Índices de tabela `produtos`
--
ALTER TABLE `produtos`
  ADD PRIMARY KEY (`id`),
  ADD KEY `id_fornecedor` (`id_fornecedor`);

--
-- Índices de tabela `usuarios`
--
ALTER TABLE `usuarios`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`),
  ADD UNIQUE KEY `cpf` (`cpf`);

--
-- Índices de tabela `vendas`
--
ALTER TABLE `vendas`
  ADD PRIMARY KEY (`id`),
  ADD KEY `id_cliente` (`id_cliente`);

--
-- Índices de tabela `venda_itens`
--
ALTER TABLE `venda_itens`
  ADD PRIMARY KEY (`id`),
  ADD KEY `venda_id` (`venda_id`),
  ADD KEY `produto_id` (`produto_id`);

--
-- AUTO_INCREMENT para tabelas despejadas
--

--
-- AUTO_INCREMENT de tabela `clientes`
--
ALTER TABLE `clientes`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT de tabela `empresa`
--
ALTER TABLE `empresa`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT de tabela `entradas_estoque`
--
ALTER TABLE `entradas_estoque`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de tabela `financeiro`
--
ALTER TABLE `financeiro`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de tabela `fornecedores`
--
ALTER TABLE `fornecedores`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT de tabela `itens_orcamento`
--
ALTER TABLE `itens_orcamento`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT de tabela `itens_venda`
--
ALTER TABLE `itens_venda`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=85;

--
-- AUTO_INCREMENT de tabela `movimentacoes_estoque`
--
ALTER TABLE `movimentacoes_estoque`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de tabela `orcamentos`
--
ALTER TABLE `orcamentos`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT de tabela `produtos`
--
ALTER TABLE `produtos`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=17;

--
-- AUTO_INCREMENT de tabela `usuarios`
--
ALTER TABLE `usuarios`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT de tabela `vendas`
--
ALTER TABLE `vendas`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=90;

--
-- AUTO_INCREMENT de tabela `venda_itens`
--
ALTER TABLE `venda_itens`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- Restrições para tabelas despejadas
--

--
-- Restrições para tabelas `entradas_estoque`
--
ALTER TABLE `entradas_estoque`
  ADD CONSTRAINT `entradas_estoque_ibfk_1` FOREIGN KEY (`produto_id`) REFERENCES `produtos` (`id`),
  ADD CONSTRAINT `entradas_estoque_ibfk_2` FOREIGN KEY (`fornecedor_id`) REFERENCES `fornecedores` (`id`),
  ADD CONSTRAINT `entradas_estoque_ibfk_3` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`);

--
-- Restrições para tabelas `financeiro`
--
ALTER TABLE `financeiro`
  ADD CONSTRAINT `financeiro_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`);

--
-- Restrições para tabelas `itens_orcamento`
--
ALTER TABLE `itens_orcamento`
  ADD CONSTRAINT `itens_orcamento_ibfk_1` FOREIGN KEY (`id_orcamento`) REFERENCES `orcamentos` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `itens_orcamento_ibfk_2` FOREIGN KEY (`id_produto`) REFERENCES `produtos` (`id`);

--
-- Restrições para tabelas `itens_venda`
--
ALTER TABLE `itens_venda`
  ADD CONSTRAINT `itens_venda_ibfk_1` FOREIGN KEY (`id_venda`) REFERENCES `vendas` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `itens_venda_ibfk_2` FOREIGN KEY (`id_produto`) REFERENCES `produtos` (`id`);

--
-- Restrições para tabelas `movimentacoes_estoque`
--
ALTER TABLE `movimentacoes_estoque`
  ADD CONSTRAINT `movimentacoes_estoque_ibfk_1` FOREIGN KEY (`produto_id`) REFERENCES `produtos` (`id`),
  ADD CONSTRAINT `movimentacoes_estoque_ibfk_2` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`);

--
-- Restrições para tabelas `orcamentos`
--
ALTER TABLE `orcamentos`
  ADD CONSTRAINT `orcamentos_ibfk_1` FOREIGN KEY (`id_cliente`) REFERENCES `clientes` (`id`);

--
-- Restrições para tabelas `produtos`
--
ALTER TABLE `produtos`
  ADD CONSTRAINT `produtos_ibfk_1` FOREIGN KEY (`id_fornecedor`) REFERENCES `fornecedores` (`id`);

--
-- Restrições para tabelas `vendas`
--
ALTER TABLE `vendas`
  ADD CONSTRAINT `vendas_ibfk_1` FOREIGN KEY (`id_cliente`) REFERENCES `clientes` (`id`);

--
-- Restrições para tabelas `venda_itens`
--
ALTER TABLE `venda_itens`
  ADD CONSTRAINT `venda_itens_ibfk_1` FOREIGN KEY (`venda_id`) REFERENCES `vendas` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `venda_itens_ibfk_2` FOREIGN KEY (`produto_id`) REFERENCES `produtos` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
