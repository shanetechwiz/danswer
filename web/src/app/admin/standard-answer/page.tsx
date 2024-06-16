"use client";

import { AdminPageTitle } from "@/components/admin/Title";
import { ClipboardIcon, EditIcon, TrashIcon } from "@/components/icons/icons";
import { PopupSpec, usePopup } from "@/components/admin/connectors/Popup";
import { useStandardAnswers } from "./hooks";
import { ThreeDotsLoader } from "@/components/Loading";
import { ErrorCallout } from "@/components/ErrorCallout";
import { Button, Text } from "@tremor/react";
import Link from "next/link";
import { StandardAnswer } from "@/lib/types";
import { MagnifyingGlass } from "@phosphor-icons/react";
import { useState } from "react";
import {
  Table,
  TableHead,
  TableRow,
  TableHeaderCell,
  TableBody,
  TableCell,
} from "@tremor/react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { deleteStandardAnswer } from "./lib";

const StandardAnswersTable = ({
  standardAnswers,
  refresh,
  setPopup,
}: {
  standardAnswers: StandardAnswer[];
  refresh: () => void;
  setPopup: (popup: PopupSpec | null) => void;
}) => {
  const [query, setQuery] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const columns = [
    { name: "", key: "edit" },
    { name: "Keyword/Phrase", key: "keyword" },
    { name: "Answer", key: "answer" },
    { name: "", key: "delete" },
  ];

  const filteredData = standardAnswers.filter((standardAnswer) => {
    const { answer, id, categories, ...fieldsToSearch } = standardAnswer;
    const cleanedQuery = query.toLowerCase();
    const searchMatch = Object.values(fieldsToSearch).some((value) => {
      return value.toLowerCase().includes(cleanedQuery);
    });
    return searchMatch;
  });

  const totalPages = Math.ceil(filteredData.length / pageSize);
  const startIndex = (currentPage - 1) * pageSize;
  const endIndex = startIndex + pageSize;
  const paginatedData = filteredData.slice(startIndex, endIndex);

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  const handleDelete = async (id: number) => {
    const response = await deleteStandardAnswer(id);
    if (response.ok) {
      setPopup({
        message: `Standard answer ${id} deleted`,
        type: "success",
      });
    } else {
      const errorMsg = await response.text();
      setPopup({
        message: `Failed to delete standard answer - ${errorMsg}`,
        type: "error",
      });
    }
    refresh();
  };

  return (
    <div className="justify-center py-2">
      <div className="flex items-center w-full border-2 border-border rounded-lg px-4 py-2 focus-within:border-accent">
        <MagnifyingGlass />
        <textarea
          autoFocus
          className="flex-grow ml-2 h-6 bg-transparent outline-none placeholder-subtle overflow-hidden whitespace-normal resize-none"
          role="textarea"
          aria-multiline
          placeholder="Find standard answers by keyword/phrase..."
          value={query}
          onChange={(event) => {
            setQuery(event.target.value);
            setCurrentPage(1);
          }}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              event.preventDefault();
            }
          }}
          suppressContentEditableWarning={true}
        />
      </div>
      <div className="mx-auto">
        <Table>
          <TableHead>
            <TableRow>
              {columns.map((column) => (
                <TableHeaderCell key={column.key}>
                  {column.name}
                </TableHeaderCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {paginatedData.map((item) => (
              <TableRow key={item.id}>
                <TableCell className="w-1/24">
                  <Link href={`/admin/standard-answer/${item.id}`}>
                    {/* <Button color="blue" size="xs">
                    Edit
                  </Button> */}
                    <EditIcon />
                  </Link>
                </TableCell>
                <TableCell className="w-2/12">{item.keyword}</TableCell>
                <TableCell className="w-9/12 overflow-auto">
                  <ReactMarkdown className="prose" remarkPlugins={[remarkGfm]}>
                    {item.answer}
                  </ReactMarkdown>
                </TableCell>
                <TableCell className="w-1/24">
                  <div
                    className="cursor-pointer"
                    onClick={() => handleDelete(item.id)}
                  >
                    <TrashIcon />
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        {paginatedData.length > 0 && (
          <div className="mt-4 flex justify-center">
            <button
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={currentPage === 1}
              className="px-3 py-2 border border-gray-300 rounded-l-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            <div className="px-3 py-2 border-t border-b border-gray-300">
              Page {currentPage} of {totalPages}
            </div>
            <button
              onClick={() => handlePageChange(currentPage + 1)}
              disabled={currentPage === totalPages}
              className="px-3 py-2 border border-gray-300 rounded-r-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

const Main = () => {
  const { popup, setPopup } = usePopup();
  const {
    data: standardAnswers,
    error: standardAnswersError,
    isLoading: standardAnswersIsLoading,
    refreshStandardAnswers,
  } = useStandardAnswers();

  if (standardAnswersIsLoading) {
    return <ThreeDotsLoader />;
  }

  if (standardAnswersError || !standardAnswers) {
    return (
      <ErrorCallout
        errorTitle="Error loading standard answers"
        errorMsg={
          standardAnswersError.info?.message ||
          standardAnswersError.message.info?.detail
        }
      />
    );
  }

  return (
    <div className="mb-8">
      {popup}

      <Text className="mb-2">
        Here you can manage the standard answers that are used to answer
        questions based on keywords or phrases.
      </Text>
      {standardAnswers.length == 0 && (
        <Text className="mb-2">Add your first standard answer below!</Text>
      )}
      <div className="mb-2"></div>

      <Link className="flex mb-3" href="/admin/standard-answer/new">
        <Button className="my-auto" color="green" size="xs">
          New Standard Answer
        </Button>
      </Link>
      <div>
        <StandardAnswersTable
          standardAnswers={standardAnswers}
          refresh={refreshStandardAnswers}
          setPopup={setPopup}
        />
      </div>
    </div>
  );
};

const Page = () => {
  return (
    <div className="container mx-auto">
      <AdminPageTitle
        icon={<ClipboardIcon size={32} />}
        title="Standard Answers"
      />
      <Main />
    </div>
  );
};

export default Page;
